"""pytest configuration and shared fixtures for the svg2tikz test suite."""

import sys
import pytest


@pytest.fixture(autouse=True)
def _isolate_argv():
    """Prevent inkex's arg_parser.parse_args() from reading pytest's sys.argv.

    inkex calls ``arg_parser.parse_args()`` (no arguments) which reads
    ``sys.argv[1:]``.  When pytest is running, that slice contains pytest's
    own flags (``-v``, ``--tb``, test paths, …) which the inkex parser does
    not recognise and raises ``SystemExit: 2``.  Replacing argv with just
    the program name for the duration of each test avoids this without
    touching library code.
    """
    saved = sys.argv
    sys.argv = sys.argv[:1]
    yield
    sys.argv = saved
