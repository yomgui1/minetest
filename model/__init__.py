# This file is part of NoCurve.
#
#    NoCurve is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    NoCurve is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with NoCurve.  If not, see <http://www.gnu.org/licenses/>.

import os
import mvc
import game

from player import MainPlayer
from math import ceil


class MapProxy(mvc.Proxy):
    NAME = 'Map'

    mcr = None

    def __init__(self, map):
        mvc.Proxy.__init__(self, map)
        self.update = map.update
        self.set_root = map.set_root

    def get_test_map(self, name):
        return getattr(self.component, "test_" + name, None)

    def add_player(self, proxy):
        self.component.add_player(proxy.component)

    def remove_player(self, proxy):
        self.component.remove_player(proxy.component)


class PlayerProxy(mvc.Proxy):
    NAME = 'Player'
