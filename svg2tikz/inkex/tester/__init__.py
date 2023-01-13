# coding=utf-8
#
# Copyright (C) 2018-2019 Martin Owens
#               2019 Thomas Holder
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
All Inkscape extensions should come with tests. This package provides you with
the tools needed to create tests and thus ensure that your extension continues
to work with future versions of Inkscape, the "inkex" python modules, and other
python and non-python tools you may use.

Make sure your extension is a python extension and is using the `inkex.generic`
base classes. These provide the greatest amount of functionality for testing.

You should start by creating a folder in your repository called `tests` with
an empty file inside called `__init__.py` to turn it into a module folder.

For each of your extensions, you should create a file called
`test_{extension_name}.py` where the name reflects the name of your extension.

There are two types of tests:

    1. Full-process Comparison tests - These are tests which invoke your
           extension with various arguments and attempt to compare the
           output to a known good reference. These are useful for testing
           that your extension would work if it was used in Inkscape.

           Good example of writing comparison tests can be found in the
           Inkscape core repository, each test which inherits from
           the ComparisonMixin class is running comparison tests.

    2. Unit tests - These are individual test functions which call out to
           specific functions within your extension. These are typical
           python unit tests and many good python documents exist
           to describe how to write them well. For examples here you
           can find the tests that test the inkex modules themselves
           to be the most instructive.

When running a test, it will cause a certain fraction of the code within the
extension to execute. This fraction called it's **coverage** and a higher
coverage score indicates that your test is better at exercising the various
options, features, and branches within your code.

Generating comparison output can be done using the EXPORT_COMPARE environment
variable when calling pytest. For example:

    EXPORT_COMPARE=1 pytest tests/test_my_specific_test.py

This will create files in `tests/data/refs/*.out.export` and these files should
be manually checked to make sure they are correct before being renamed and stripped
of the `.export` suffix. pytest should then be re-run to confirm before
committing to the repository.
"""

from __future__ import absolute_import, print_function, unicode_literals

import os
import re
import sys
import shutil
import tempfile
import hashlib
import random
import uuid

from io import BytesIO, StringIO
import xml.etree.ElementTree as xml

from unittest import TestCase as BaseCase
from inkex.base import InkscapeExtension

from ..utils import PY3, to_bytes
from .xmldiff import xmldiff
from .mock import MockCommandMixin, Capture

if False: # pylint: disable=using-constant-test
    from typing import Type, List
    from .filters import Compare


class NoExtension(InkscapeExtension):  # pylint: disable=too-few-public-methods
    """Test case must specify 'self.effect_class' to assertEffect."""

    def __init__(self, *args, **kwargs): # pylint: disable=super-init-not-called
        raise NotImplementedError(self.__doc__)

    def run(self, args=None, output=None):
        """Fake run"""
        pass


class TestCase(MockCommandMixin, BaseCase):
    """
    Base class for all effects tests, provides access to data_files and test_without_parameters
    """
    effect_class = NoExtension # type: Type[InkscapeExtension]
    effect_name = property(lambda self: self.effect_class.__module__)

    # If set to true, the output is not expected to be the stdout SVG document, but rather
    # text or a message sent to the stderr, this is highly weird. But sometimes happens.
    stderr_output = False
    stdout_protect = True
    stderr_protect = True
    python3_only = False

    def __init__(self, *args, **kw):
        super(TestCase, self).__init__(*args, **kw)
        self._temp_dir = None
        self._effect = None

    def setUp(self): # pylint: disable=invalid-name
        """Make sure every test is seeded the same way"""
        self._effect = None
        super(TestCase, self).setUp()
        if self.python3_only and not PY3:
            self.skipTest("No available in python2")
        try:
            # python3, with version 1 to get the same numbers
            # as in python2 during tests.
            random.seed(0x35f, version=1)
        except TypeError:
            # But of course this kwarg doesn't exist in python2
            random.seed(0x35f)

    def tearDown(self):
        super(TestCase, self).tearDown()
        if self._temp_dir and os.path.isdir(self._temp_dir):
            shutil.rmtree(self._temp_dir)

    @classmethod
    def __file__(cls):
        """Create a __file__ property which acts much like the module version"""
        return os.path.abspath(sys.modules[cls.__module__].__file__)

    @classmethod
    def _testdir(cls):
        """Get's the folder where the test exists (so data can be found)"""
        return os.path.dirname(cls.__file__())

    @classmethod
    def rootdir(cls):
        """Return the full path to the extensions directory"""
        return os.path.dirname(cls._testdir())

    @classmethod
    def datadir(cls):
        """Get the data directory (can be over-ridden if needed)"""
        return os.path.join(cls._testdir(), 'data')

    @property
    def tempdir(self):
        """Generate a temporary location to store files"""
        if self._temp_dir is None:
            self._temp_dir = tempfile.mkdtemp(prefix='inkex-tests-')
        if not os.path.isdir(self._temp_dir):
            raise IOError("The temporary directory has disappeared!")
        return self._temp_dir

    def temp_file(self, prefix='file-', template='{prefix}{name}{suffix}', suffix='.tmp'):
        """Generate the filename of a temporary file"""
        filename = template.format(prefix=prefix, suffix=suffix, name=uuid.uuid4().hex)
        return os.path.join(self.tempdir, filename)

    @classmethod
    def data_file(cls, filename, *parts):
        """Provide a data file from a filename, can accept directories as arguments."""
        if os.path.isabs(filename):
            # Absolute root was passed in, so we trust that (it might be a tempdir)
            full_path = os.path.join(filename, *parts)
        else:
            # Otherwise we assume it's relative to the test data dir.
            full_path = os.path.join(cls.datadir(), filename, *parts)

        if not os.path.isfile(full_path):
            raise IOError("Can't find test data file: {}".format(full_path))
        return full_path

    @property
    def empty_svg(self):
        """Returns a common minimal svg file"""
        return self.data_file('svg', 'default-inkscape-SVG.svg')

    def assertAlmostTuple(self, found, expected, precision=8): # pylint: disable=invalid-name
        """
        Floating point results may vary with computer architecture; use
        assertAlmostEqual to allow a tolerance in the result.
        """
        self.assertEqual(len(found), len(expected))
        for fon, exp in zip(found, expected):
            self.assertAlmostEqual(fon, exp, precision)

    def assertEffectEmpty(self, effect, **kwargs):  # pylint: disable=invalid-name
        """Assert calling effect without any arguments"""
        self.assertEffect(effect=effect, **kwargs)

    def assertEffect(self, *filename, **kwargs):  # pylint: disable=invalid-name
        """Assert an effect, capturing the output to stdout.

           filename should point to a starting svg document, default is empty_svg
        """
        effect = kwargs.pop('effect', self.effect_class)()

        args = [self.data_file(*filename)] if filename else [self.empty_svg]  # pylint: disable=no-value-for-parameter
        args += kwargs.pop('args', [])
        args += ['--{}={}'.format(*kw) for kw in kwargs.items()]

        # Output is redirected to this string io buffer
        if self.stderr_output:
            with Capture('stderr') as stderr:
                effect.run(args, output=BytesIO())
                effect.test_output = stderr
        else:
            output = BytesIO()
            with Capture('stdout', kwargs.get('stdout_protect', self.stdout_protect)) as stdout:
                with Capture('stderr', kwargs.get('stderr_protect', self.stderr_protect)) as stderr:
                    effect.run(args, output=output)
                    self.assertEqual('', stdout.getvalue(), "Extra print statements detected")
                    self.assertEqual('', stderr.getvalue(), "Extra error or warnings detected")
            effect.test_output = output

        if os.environ.get('FAIL_ON_DEPRECATION', False):
            warnings = getattr(effect, 'warned_about', set())
            effect.warned_about = set()  # reset for next test
            self.assertFalse(warnings, "Deprecated API is still being used!")

        return effect

    def assertDeepAlmostEqual(self, first, second, places=None, msg=None, delta=None):
        if delta is None and places is None:
            places = 7
        if isinstance(first, (list, tuple)):
            assert len(first) == len(second)
            for (f, s) in zip(first, second):
                self.assertDeepAlmostEqual(f, s, places, msg, delta)
        else:
            self.assertAlmostEqual(first, second, places, msg, delta)

    @property
    def effect(self):
        """Generate an effect object"""
        if self._effect is None:
            self._effect = self.effect_class()
        return self._effect

class InkscapeExtensionTestMixin(object):
    """Automatically setup self.effect for each test and test with an empty svg"""
    def setUp(self): # pylint: disable=invalid-name
        """Check if there is an effect_class set and create self.effect if it is"""
        super(InkscapeExtensionTestMixin, self).setUp()
        if self.effect_class is None:
            self.skipTest('self.effect_class is not defined for this this test')

    def test_default_settings(self):
        """Extension works with empty svg file"""
        self.effect.run([self.empty_svg])

class ComparisonMixin(object):
    """
    Add comparison tests to any existing test suite.
    """
    # This input svg file sent to the extension (if any)
    compare_file = 'svg/shapes.svg'
    # The ways in which the output is filtered for comparision (see filters.py)
    compare_filters = [] # type: List[Compare]
    # If true, the filtered output will be saved and only applied to the
    # extension output (and not to the reference file)
    compare_filter_save = False
    # A list of comparison runs, each entry will cause the extension to be run.
    comparisons = [
        (),
        ('--id=p1', '--id=r3'),
    ]

    def test_all_comparisons(self):
        """Testing all comparisons"""
        if not isinstance(self.compare_file, (list, tuple)):
            self._test_comparisons(self.compare_file)
        else:
            for compare_file in self.compare_file:
                self._test_comparisons(
                    compare_file,
                    addout=os.path.basename(compare_file)
                )

    def _test_comparisons(self, compare_file, addout=None):
        for args in self.comparisons:
            self.assertCompare(
                compare_file,
                self.get_compare_outfile(args, addout),
                args,
            )

    def assertCompare(self, infile, outfile, args): #pylint: disable=invalid-name
        """
        Compare the output of a previous run against this one.

         - infile: The filename of the pre-processed svg (or other type of file)
         - outfile: The filename of the data we expect to get, if not set
                    the filename will be generated from the effect name and kwargs.
         - args: All the arguments to be passed to the effect run

        """
        effect = self.assertEffect(infile, args=args)

        if outfile is None:
            outfile = self.get_compare_outfile(args)

        if not os.path.isfile(outfile):
            raise IOError("Comparison file {} not found".format(outfile))

        data_a = effect.test_output.getvalue()
        if os.environ.get('EXPORT_COMPARE', False):
            with open(outfile + '.export', 'wb') as fhl:
                if sys.version_info[0] == 3 and isinstance(data_a, str):
                    data_a = data_a.encode('utf-8')
                fhl.write(self._apply_compare_filters(data_a, True))
                print("Written output: {}.export".format(outfile))

        data_a = self._apply_compare_filters(data_a)

        with open(outfile, 'rb') as fhl:
            data_b = self._apply_compare_filters(fhl.read(), False)

        if isinstance(data_a, bytes) and isinstance(data_b, bytes) \
            and data_a.startswith(b'<') and data_b.startswith(b'<'):
            # Late importing
            diff_xml, delta = xmldiff(data_a, data_b)
            if not delta and not os.environ.get('EXPORT_COMPARE', False):
                print('The XML is different, you can save the output using the EXPORT_COMPARE=1'\
                      ' envionment variable. This will save the compared file as a ".output" file'\
                      ' next to the reference file used in the test.\n')
            diff = 'SVG Differences: {}\n\n'.format(outfile)
            if os.environ.get('XML_DIFF', False):
                diff = '<- ' + diff_xml
            else:
                for x, (value_a, value_b) in enumerate(delta):
                    try:
                        # Take advantage of better text diff in testcase's own asserts.
                        self.assertEqual(value_a, value_b)
                    except AssertionError as err:
                        diff += " {}. {}\n".format(x, str(err))
            self.assertTrue(delta, diff)
        else:
            # compare any content (non svg)
            self.assertEqual(data_a, data_b)

    def _apply_compare_filters(self, data, is_saving=None):
        data = to_bytes(data)
        # Applying filters flips depending if we are saving the filtered content
        # to disk, or filtering during the test run. This is because some filters
        # are destructive others are useful for diagnostics.
        if is_saving is self.compare_filter_save or is_saving is None:
            for cfilter in self.compare_filters:
                data = cfilter(data)
        return data

    def get_compare_outfile(self, args, addout=None):
        """Generate an output file for the arguments given"""
        if addout is not None:
            args = list(args) + [str(addout)]
        opstr = '__'.join(args)\
                    .replace(self.tempdir, 'TMP_DIR')\
                    .replace(self.datadir(), 'DAT_DIR')
        opstr = re.sub(r'[^\w-]', '__', opstr)
        if opstr:
            if len(opstr) > 127:
                # avoid filename-too-long error
                opstr = hashlib.md5(opstr.encode('latin1')).hexdigest()
            opstr = '__' + opstr
        return self.data_file("refs", "{}{}.out".format(self.effect_name, opstr))
