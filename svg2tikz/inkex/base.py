# coding=utf-8
#
# Copyright (c) 2018 - Martin Owens <doctormo@gmail.com>
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
The ultimate base functionality for every Inkscape extension.
"""
from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
import copy
import shutil

from argparse import ArgumentParser, Namespace
from lxml import etree

from .utils import PY3, filename_arg, AbortExtension, ABORT_STATUS, errormsg, do_nothing
from .elements._base import load_svg, BaseElement # pylint: disable=unused-import
from .localization import localize

stdout = sys.stdout

try:
    from typing import (List, Tuple, Type, Optional, Callable, Any, Union, IO,
                        TYPE_CHECKING, cast)
except ImportError:
    cast = lambda x, y: y
    TYPE_CHECKING = False

if PY3:
    unicode = str  # pylint: disable=redefined-builtin,invalid-name
    basestring = str  # pylint: disable=redefined-builtin,invalid-name
    stdout = sys.stdout.buffer  # type: ignore


class InkscapeExtension(object):
    """
    The base class extension, provides argument parsing and basic
    variable handling features.
    """
    multi_inx = False # Set to true if this class is used by multiple inx files.

    def __init__(self):
        # type: () -> None
        self.file_io = None # type: Optional[IO]
        self.options = Namespace()
        self.document = None # type: Union[None, bytes, str, unicode, etree]
        self.arg_parser = ArgumentParser(description=self.__doc__)

        self.arg_parser.add_argument(
            "input_file", nargs="?", metavar="INPUT_FILE", type=filename_arg,
            help="Filename of the input file (default is stdin)", default=None)

        self.arg_parser.add_argument(
            "--output", type=str, default=None,
            help="Optional output filename for saving the result (default is stdout).")

        self.add_arguments(self.arg_parser)

        localize()

    def add_arguments(self, pars):
        # type: (ArgumentParser) -> None
        """Add any extra arguments to your extension handle, use:

        def add_arguments(self, pars):
            pars.add_argument("--num-cool-things", type=int, default=3)
            pars.add_argument("--pos-in-doc", type=str, default="doobry")
        """
        pass  # No extra arguments by default so super is not required

    def parse_arguments(self, args):
        # type: (List[str]) -> None
        """Parse the given arguments and set 'self.options'"""
        self.options = self.arg_parser.parse_args(args)

    def arg_method(self, prefix='method'):
        # type: (str) -> Callable[[str], Callable[[Any], Any]]
        """Used by add_argument to match a tab selection with an object method

        pars.add_argument("--tab", type=self.arg_method(), default="foo")
        ...
        self.options.tab(arguments)
        ...
        .. code-block:: python
        .. def method_foo(self, arguments):
        ..     # do something
        """
        def _inner(value):
            name = '{}_{}'.format(prefix, value.strip('"').lower()).replace('-', '_')
            try:
                return getattr(self, name)
            except AttributeError:
                if name.startswith('_'):
                    return do_nothing
                raise AbortExtension("Can not find method {}".format(name))
        return _inner

    def debug(self, msg):
        # type: (str) -> None
        """Write a debug message"""
        errormsg("DEBUG<{}> {}\n".format(type(self).__name__, msg))

    @staticmethod
    def msg(msg):
        # type: (str) -> None
        """Write a non-error message"""
        errormsg(msg)

    def run(self, args=None, output=stdout):
        # type: (Optional[List[str]], Union[str, IO]) -> None
        """Main entrypoint for any Inkscape Extension"""
        try:
            if args is None:
                args = sys.argv[1:]

            self.parse_arguments(args)
            if self.options.input_file is None:
                self.options.input_file = sys.stdin

            if self.options.output is None:
                # assert output
                self.options.output = output

            self.load_raw()
            self.save_raw(self.effect())
        except AbortExtension as err:
            err.write()
            sys.exit(ABORT_STATUS)
        finally:
            self.clean_up()

    def load_raw(self):
        # type: () -> None
        """Load the input stream or filename, save everything to self"""
        if isinstance(self.options.input_file, (str, unicode)):
            self.file_io = open(self.options.input_file, 'rb')
            document = self.load(self.file_io)
        else:
            document = self.load(self.options.input_file)
        self.document = document

    def save_raw(self, ret):
        # type: (Any) -> None
        """Save to the output stream, use everything from self"""
        if self.has_changed(ret):
            if isinstance(self.options.output, (str, unicode)):
                with open(self.options.output, 'wb') as stream:
                    self.save(stream)
            else:
                self.save(self.options.output)

    def load(self, stream):
        # type: (IO) -> str 
        """Takes the input stream and creates a document for parsing"""
        raise NotImplementedError("No input handle for {}".format(self.name))

    def save(self, stream):
        # type: (IO) -> None 
        """Save the given document to the output file"""
        raise NotImplementedError("No output handle for {}".format(self.name))

    def effect(self):
        # type: () -> Any 
        """Apply some effects on the document or local context"""
        raise NotImplementedError("No effect handle for {}".format(self.name))

    def has_changed(self, ret): # pylint: disable=no-self-use
        # type: (Any) -> bool
        """Return true if the output should be saved"""
        return ret is not False

    def clean_up(self):
        # type: () -> None
        """Clean up any open handles and other items"""
        if self.file_io is not None:
            self.file_io.close()

    def svg_path(self):
        # type: () -> Optional[str]
        """
        Return the folder the svg is contained in.
        Returns None if there is no file.
        """
        if self.options.input_file:
            return os.path.dirname(self.options.input_file)
        return None

    @classmethod
    def ext_path(cls):
        # type: () -> str
        """Return the folder the extension script is in"""
        return os.path.dirname(sys.modules[cls.__module__].__file__)

    @classmethod
    def get_resource(cls, name, abort_on_fail=True):
        # type: (str, bool) -> str
        """Return the full filename of the resource in the extension's dir"""
        filename = os.path.join(cls.ext_path(), name)
        if abort_on_fail and not os.path.isfile(filename):
            raise AbortExtension(f"Could not find resource file: {filename}")
        return filename

    def absolute_href(self, filename, default='~/'):
        # type: (str, str) -> str
        """
        Process the filename such that it's turned into an absolute filename
        with the working directory being the directory of the loaded svg.

        User's home folder is also resolved. So '~/a.png` will be `/home/bob/a.png`

        Default is a fallback directory to use if the svg's filename is not available.
        """
        filename = os.path.expanduser(filename)
        if not os.path.isabs(filename):
            path = self.svg_path() or default
            filename = os.path.join(path, filename)
        return os.path.realpath(os.path.expanduser(filename))

    @property
    def name(self):
        # type: () -> str
        """Return a fixed name for this extension"""
        return type(self).__name__


if TYPE_CHECKING:
    _Base = InkscapeExtension
else:
    _Base = object


class TempDirMixin(_Base):
    """
    Provide a temporary directory for extensions to stash files.
    """
    dir_suffix = ''
    dir_prefix = 'inktmp'

    def __init__(self, *args, **kwargs):
        self.tempdir = None
        super(TempDirMixin, self).__init__(*args, **kwargs)

    def load_raw(self):
        # type: () -> None
        """Create the temporary directory"""
        from tempfile import mkdtemp
        self.tempdir = mkdtemp(self.dir_suffix, self.dir_prefix, None)
        super(TempDirMixin, self).load_raw()

    def clean_up(self):
        # type: () -> None
        """Delete the temporary directory"""
        if self.tempdir and os.path.isdir(self.tempdir):
            shutil.rmtree(self.tempdir)
        super(TempDirMixin, self).clean_up()


class SvgInputMixin(_Base):  # pylint: disable=too-few-public-methods
    """
    Expects the file input to be an svg document and will parse it.
    """
    # Select all objects if none are selected
    select_all = () # type: Tuple[Type[BaseElement], ...]

    def __init__(self):
        super(SvgInputMixin, self).__init__()

        self.arg_parser.add_argument(
            "--id", action="append", type=str, dest="ids", default=[],
            help="id attribute of object to manipulate")

        self.arg_parser.add_argument(
            "--selected-nodes", action="append", type=str, dest="selected_nodes", default=[],
            help="id:subpath:position of selected nodes, if any")

    def load(self, stream):
        # type: (IO) -> etree
        """Load the stream as an svg xml etree and make a backup"""
        document = load_svg(stream)
        self.original_document = copy.deepcopy(document)
        self.svg = document.getroot()
        self.svg.selection.set(*self.options.ids)
        if not self.svg.selection and self.select_all:
            self.svg.selection = self.svg.descendants().filter(*self.select_all)
        return document


class SvgOutputMixin(_Base):  # pylint: disable=too-few-public-methods
    """
    Expects the output document to be an svg document and will write an etree xml.

    A template can be specified to kick off the svg document building process.
    """
    template = """<svg viewBox="0 0 {width} {height}" width="{width}{unit}" height="{height}{unit}"
        xmlns="http://www.w3.org/2000/svg" xmlns:svg="http://www.w3.org/2000/svg"
        xmlns:xlink="http://www.w3.org/1999/xlink"
        xmlns:sodipodi="http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd"
        xmlns:inkscape="http://www.inkscape.org/namespaces/inkscape">
    </svg>"""

    @classmethod
    def get_template(cls, **kwargs):
        """
        Opens a template svg document for building, the kwargs
        MUST include all the replacement values in the template, the
        default template has 'width' and 'height' of the document.
        """
        kwargs.setdefault('unit', '')
        return load_svg(str(cls.template.format(**kwargs)))

    def save(self, stream):
        # type: (IO) -> None
        """Save the svg document to the given stream"""
        if isinstance(self.document, (bytes, str, unicode)):
            document = self.document
        elif 'Element' in type(self.document).__name__:
            # isinstance can't be used here because etree is broken
            doc = cast(etree, self.document)
            document = doc.getroot().tostring()
        else:
            raise ValueError("Unknown type of document: {} can not save."\
                .format(type(self.document).__name__))

        try:
            stream.write(document)
        except TypeError:
            # we hope that this happens only when document needs to be encoded
            stream.write(document.encode('utf-8')) # type: ignore

class SvgThroughMixin(SvgInputMixin, SvgOutputMixin):
    """
    Combine the input and output svg document handling (usually for effects).
    """

    def has_changed(self, ret): # pylint: disable=unused-argument
        # type: (Any) -> bool
        """Return true if the svg document has changed"""
        original = etree.tostring(self.original_document)
        result = etree.tostring(self.document)
        return original != result
