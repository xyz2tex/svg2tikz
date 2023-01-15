# coding=utf-8
"""
This describes the core API for the inkex core modules.

This provides the basis from which you can develop your inkscape extension.
"""

# pylint: disable=wildcard-import
from __future__ import print_function

from .extensions import *
from .utils import *
from .styles import *
from .paths import Path, CubicSuperPath  # Path commands are not exported
from .colors import *
from .transforms import *
from .elements import *

# legacy proxies
from .deprecated import Effect
from .deprecated import optparse
from .deprecated import InkOption
from .deprecated import etree
from .deprecated import localize
from .deprecated import debug

# legacy functions
from .deprecated import are_near_relative
from .deprecated import unittouu
