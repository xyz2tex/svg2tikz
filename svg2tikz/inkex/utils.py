# coding=utf-8
#
# Copyright (C) 2010 Nick Drobchenko, nick@cnc-club.ru
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
Basic common utility functions for calculated things
"""
from __future__ import absolute_import, print_function, unicode_literals

import os
import sys
import shutil
import random
import math

from itertools import tee
from collections import defaultdict
from argparse import ArgumentTypeError

# When python2 support is gone, enable tempfile's version
# from tempfile import TemporaryDirectory

# All the names that get added to the inkex API itself.
__all__ = ('AbortExtension', 'DependencyError', 'Boolean', 'errormsg', 'addNS', 'NSS')

ABORT_STATUS = -5

(X, Y) = range(2)
PY3 = sys.version_info[0] == 3

if PY3:
    unicode = str  # pylint: disable=redefined-builtin,invalid-name

# a dictionary of all of the xmlns prefixes in a standard inkscape doc
NSS = {
    'sodipodi': 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd',
    'cc': 'http://creativecommons.org/ns#',
    'ccOLD': 'http://web.resource.org/cc/',
    'svg': 'http://www.w3.org/2000/svg',
    'dc': 'http://purl.org/dc/elements/1.1/',
    'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
    'inkscape': 'http://www.inkscape.org/namespaces/inkscape',
    'xlink': 'http://www.w3.org/1999/xlink',
    'xml': 'http://www.w3.org/XML/1998/namespace'
}
SSN = dict((b, a) for (a, b) in NSS.items())

def _pythonpath():
    for pth in os.environ.get('PYTHONPATH', '').split(':'):
        if os.path.isdir(pth):
            yield pth

def get_user_directory():
    """Return the user directory where extensions are stored."""
    if 'INKSCAPE_PROFILE_DIR' in os.environ:
        return os.path.abspath(
            os.path.expanduser(
                os.path.join(os.environ['INKSCAPE_PROFILE_DIR'], 'extensions')))

    home = os.path.expanduser("~")
    for pth in _pythonpath():
        if pth.startswith(home):
            return pth

def get_inkscape_directory():
    """Return the system directory where inkscape's core is."""
    for pth in _pythonpath():
        if os.path.isdir(os.path.join(pth, 'inkex')):
            return pth

class KeyDict(dict):
    """
    A normal dictionary, except asking for anything not in the dictionary
    always returns the key itself. This is used for translation dictionaries.
    """
    def __getitem__(self, key):
        try:
            return super(KeyDict, self).__getitem__(key)
        except KeyError:
            return key

class TemporaryDirectory(object): # pylint: disable=too-few-public-methods
    """Tiny replacement for python3's version."""
    def __init__(self, suffix="", prefix="tmp"):
        self.suffix = suffix
        self.prefix = prefix
        self.path = None
    def __enter__(self):
        from tempfile import mkdtemp
        self.path = mkdtemp(self.suffix, self.prefix, None)
        return self.path
    def __exit__(self, exc, value, traceback):
        if os.path.isdir(self.path):
            shutil.rmtree(self.path)

def Boolean(value):
    """ArgParser function to turn a boolean string into a python boolean"""
    if value.upper() == 'TRUE':
        return True
    elif value.upper() == 'FALSE':
        return False
    return None

def to_bytes(content):
    """Ensures the content is bytes"""
    if isinstance(content, bytes):
        return content
    return str(content).encode("utf8")

def debug(what):
    """Print debug message if debugging is switched on"""
    errormsg(what)
    return what

def do_nothing(*args, **kwargs): # pylint: disable=unused-argument
    """A blank function to do nothing"""
    pass

def errormsg(msg):
    """Intended for end-user-visible error messages.

       (Currently just writes to stderr with an appended newline, but could do
       something better in future: e.g. could add markup to distinguish error
       messages from status messages or debugging output.)

       Note that this should always be combined with translation:

         import inkex
         ...
         inkex.errormsg(_("This extension requires two selected paths."))
    """
    try:
        sys.stderr.write(msg)
    except TypeError:
        sys.stderr.write(unicode(msg))
    except UnicodeEncodeError:
        # Python 2:
        # Fallback for cases where sys.stderr.encoding is not Unicode.
        # Python 3:
        # This will not work as write() does not accept byte strings, but AFAIK
        # we should never reach this point as the default error handler is
        # 'backslashreplace'.

        # This will be None by default if stderr is piped, so use ASCII as a
        # last resort.
        encoding = sys.stderr.encoding or 'ascii'
        sys.stderr.write(msg.encode(encoding, 'backslashreplace'))

    # Write '\n' separately to avoid dealing with different string types.
    sys.stderr.write('\n')


class AbortExtension(Exception):
    """Raised to print a message to the user without backtrace"""

    def __init__(self, message=""):
        self.message = message

    def write(self):
        """write the error message out to the user"""
        errormsg(self.message)


class DependencyError(NotImplementedError):
    """Raised when we need an external python module that isn't available"""

class FragmentError(Exception):
    """Raised when trying to do rooty things on an xml fragment"""

def to(kind):  # pylint: disable=invalid-name
    """
    Decorator which will turn a generator into a list, tuple or other object type.
    """

    def _inner(call):
        def _outer(*args, **kw):
            return kind(call(*args, **kw))

        return _outer

    return _inner


def strargs(string, kind=float):
    """Returns a list of floats from a string with commas or space separators, 
        also splits at -(minus) signs by adding a space in front of the - sign
    """
    return [kind(val) for val in string.replace(',', ' ').replace('-', ' -').replace('e ', 'e').split()]


def addNS(tag, ns=None):  # pylint: disable=invalid-name
    """Add a known namespace to a name for use with lxml"""
    if tag.startswith('{') and ns:
        _, tag = removeNS(tag)
    if not tag.startswith('{'):
        tag = tag.replace('__', ':')
        if ':' in tag:
            (ns, tag) = tag.rsplit(':', 1)
        if ns in NSS:
            ns = NSS[ns]
        if ns is not None:
            return "{%s}%s" % (ns, tag)
    return tag


def removeNS(name):  # pylint: disable=invalid-name
    """The reverse of addNS, finds any namespace and returns tuple (ns, tag)"""
    if name[0] == '{':
        (url, tag) = name[1:].split('}', 1)
        return SSN.get(url, 'svg'), tag
    if ':' in name:
        return name.rsplit(':', 1)
    return 'svg', name

def splitNS(name): # pylint: disable=invalid-name
    """Like removeNS, but returns a url instead of a prefix"""
    (prefix, tag) = removeNS(name)
    return (NSS[prefix], tag)

class classproperty(object):  # pylint: disable=invalid-name, too-few-public-methods
    """Combine classmethod and property decorators"""

    def __init__(self, func):
        self.func = func

    def __get__(self, obj, owner):
        return self.func(owner)


def filename_arg(name):
    """Existing file to read or option used in script arguments"""
    filename = os.path.abspath(os.path.expanduser(name))
    if not os.path.isfile(filename):
        raise ArgumentTypeError("File not found: {}".format(name))
    return filename

def pairwise(iterable, start=True):
    "Iterate over a list with overlapping pairs (see itertools recipes)"
    first, then = tee(iterable)
    starter = [(None, next(then, None))]
    if not start:
        starter = []
    return starter + list(zip(first, then))

class CloningVat(object):
    """
    When modifying defs, sometimes we want to know if every backlink would have
    needed changing, or it was just some of them.

    This tracks the def elements, their promises and creates clones if needed.
    """
    def __init__(self, svg):
        self.svg = svg
        self.tracks = defaultdict(set)
        self.set_ids = defaultdict(list)

    def track(self, elem, parent, set_id=None, **kwargs):
        """Track the element and connected parent"""
        elem_id = elem.get('id')
        parent_id = parent.get('id')
        self.tracks[elem_id].add(parent_id)
        self.set_ids[elem_id].append((set_id, kwargs))

    def process(self, process, types=(), make_clones=True, **kwargs):
        """
        Process each tracked item if the backlinks match the parents

        Optionally make clones, process the clone and set the new id.
        """
        for elem_id in list(self.tracks):
            parents = self.tracks[elem_id]
            elem = self.svg.getElementById(elem_id)
            backlinks = set([blk.get('id') for blk in elem.backlinks(*types)])
            if backlinks == parents:
                # No need to clone, we're processing on-behalf of all parents
                process(elem, **kwargs)
            elif make_clones:
                clone = elem.copy()
                elem.getparent().append(clone)
                clone.set_random_id()
                for update, upkw in self.set_ids.get(elem_id, ()):
                    update(elem.get('id'), clone.get('id'), **upkw)
                process(clone, **kwargs)

EVAL_GLOBALS = {}
EVAL_GLOBALS.update(random.__dict__)
EVAL_GLOBALS.update(math.__dict__)

def math_eval(function, variable="x"):
    """Interpret a function string. All functions from math and random may be used.
    @returns a lambda expression if sucessful; otherwise None.
    """
    try:
        if function != "":
            return eval(f'lambda {variable}: ' + (function.strip('"') or 't'), EVAL_GLOBALS, {})
    # handle incomplete/invalid function gracefully
    except SyntaxError:
        pass
    return None
