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

import math
import random


class pTurtle(object):
    """A Python path turtle"""

    def __init__(self, home=(0, 0)):
        self.__home = [home[0], home[1]]
        self.__pos = self.__home[:]
        self.__heading = -90
        self.__path = ""
        self.__draw = True
        self.__new = True

    def forward(self, mag):
        self.setpos((self.__pos[0] + math.cos(math.radians(self.__heading)) * mag,
                     self.__pos[1] + math.sin(math.radians(self.__heading)) * mag))

    def backward(self, mag):
        self.setpos((self.__pos[0] - math.cos(math.radians(self.__heading)) * mag,
                     self.__pos[1] - math.sin(math.radians(self.__heading)) * mag))

    def right(self, deg):
        self.__heading -= deg

    def left(self, deg):
        self.__heading += deg

    def penup(self):
        self.__draw = False
        self.__new = False

    def pendown(self):
        if not self.__draw:
            self.__new = True
        self.__draw = True

    def pentoggle(self):
        if self.__draw:
            self.penup()
        else:
            self.pendown()

    def home(self):
        self.setpos(self.__home)

    def clean(self):
        self.__path = ''

    def clear(self):
        self.clean()
        self.home()

    def setpos(self, arg):
        if self.__new:
            self.__path += "M" + ",".join([str(i) for i in self.__pos])
            self.__new = False
        self.__pos = arg
        if self.__draw:
            self.__path += "L" + ",".join([str(i) for i in self.__pos])

    def getpos(self):
        return self.__pos[:]

    def setheading(self, deg):
        self.__heading = deg

    def getheading(self):
        return self.__heading

    def sethome(self, arg):
        self.__home = list(arg)

    def getPath(self):
        return self.__path

    def rtree(self, size, minimum, pt=False):
        if size < minimum:
            return
        self.fd(size)
        turn = random.uniform(20, 40)
        self.lt(turn)
        self.rtree(size * random.uniform(0.5, 0.9), minimum, pt)
        self.rt(turn)
        turn = random.uniform(20, 40)
        self.rt(turn)
        self.rtree(size * random.uniform(0.5, 0.9), minimum, pt)
        self.lt(turn)
        if pt:
            self.pu()
        self.bk(size)
        if pt:
            self.pd()

    fd = forward
    bk = backward
    rt = right
    lt = left
    pu = penup
    pd = pendown
