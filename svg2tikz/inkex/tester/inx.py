#!/usr/bin/env python
# coding=utf-8
"""
Test elements extra logic from svg xml lxml custom classes.
"""

from ..utils import PY3
from ..inx import InxFile

INTERNAL_ARGS = ('help', 'output', 'id', 'selected-nodes')
ARG_TYPES = {
    'Boolean': 'bool',
    'Color': 'color',
    'str': 'string',
    'int': 'int',
    'float': 'float',
}

class InxMixin(object):
    """Tools for Testing INX files, use as a mixin class:

    class MyTests(InxMixin, TestCase):
        def test_inx_file(self):
            self.assertInxIsGood("some_inx_file.inx")
    """
    def assertInxIsGood(self, inx_file): # pylint: disable=invalid-name
        """Test the inx file for consistancy and correctness"""
        self.assertTrue(PY3, "INX files can only be tested in python3")

        inx = InxFile(inx_file)
        if 'help' in inx.ident or inx.script.get('interpreter', None) != 'python':
            return
        cls = inx.extension_class
        # Check class can be matched in python file
        self.assertTrue(cls, 'Can not find class for {}'.format(inx.filename))
        # Check name is reasonable for the class
        if not cls.multi_inx:
            self.assertEqual(
                cls.__name__, inx.slug,
                "Name of extension class {}.{} is different from ident {}".format(
                    cls.__module__, cls.__name__, inx.slug))
            self.assertParams(inx, cls)

    def assertParams(self, inx, cls): # pylint: disable=invalid-name
        """Confirm the params in the inx match the python script"""
        params = dict([(param.name, self.parse_param(param)) for param in inx.params])
        args = dict(self.introspect_arg_parser(cls().arg_parser))
        mismatch_a = list(set(params) ^ set(args) & set(params))
        mismatch_b = list(set(args) ^ set(params) & set(args))
        self.assertFalse(mismatch_a, "{}: Inx params missing from arg parser".format(inx.filename))
        self.assertFalse(mismatch_b, "{}: Script args missing from inx xml".format(inx.filename))

        for param in args:
            if params[param]['type'] and args[param]['type']:
                self.assertEqual(
                    params[param]['type'],
                    args[param]['type'],
                    "Type is not the same for {}:param:{}".format(inx.filename, param))

    def introspect_arg_parser(self, arg_parser):
        """Pull apart the arg parser to find out what we have in it"""
        for action in arg_parser._optionals._actions: # pylint: disable=protected-access
            for opt in action.option_strings:
                # Ignore params internal to inkscape (thus not in the inx)
                if opt.startswith('--') and opt[2:] not in INTERNAL_ARGS:
                    yield (opt[2:], self.introspect_action(action))

    @staticmethod
    def introspect_action(action):
        """Pull apart a single action to get at the juicy insides"""
        return {
            'type': ARG_TYPES.get((action.type or str).__name__, 'string'),
            'default': action.default,
            'choices': action.choices,
            'help': action.help,
        }

    @staticmethod
    def parse_param(param):
        """Pull apart the param element in the inx file"""
        if param.param_type in ('optiongroup', 'notebook'):
            options = param.options
            return {
                'type': None,
                'choices': options,
                'default': options and options[0] or None,
            }
        param_type = param.param_type
        if param.param_type in ('path',):
            param_type = 'string'
        return {
            'type': param_type,
            'default': param.text,
            'choices': None,
        }
