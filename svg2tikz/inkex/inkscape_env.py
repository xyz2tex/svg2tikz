# coding=utf-8
#
# Copyright (C) 2020 Martin Owens <doctormo@geek-2.com>
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
Import this inkex module if you are using the extension manager
and need virtualenv dependencies. Things like gobject, numpy etc

Always import *before* anything else.
"""

import os
import sys

def get_bin(fname):
    """Get a virtualenv binary for execution, returns full filename"""
    for path in sys.path:
        for script in [fname, os.path.join('bin', fname)]:
            result = os.path.abspath(os.path.join(path, script))
            if os.path.isfile(result):
                return result
    return None

def activate_virtualenv():
    """ 
    The python that inkscape uses and the python installed into the virtualenv
    are different pythons with different libs. To give access to dependencies
    that are installed within the virtualenv, we activate the available venv.
    """
    activate_this = get_bin('activate_this.py')
    if os.path.isfile(activate_this):
        with open(activate_this, 'r') as fhl:
            exec(fhl.read(), dict(__file__=activate_this))
        return

activate_virtualenv()
