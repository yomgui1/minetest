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

import lowlevel

MIN_FAC = [(0, 0, 0), (0, 1, 0), (1, 0, 0), (1, 1, 0), (0, 0, 1), (0, 1, 1), (1, 0, 1), (1, 1, 1)]

class Cluster(lowlevel.Cluster):
    """Class to manipulate an internal Cluster structure.
    """

    __slots__ = ['_level']

    def __new__(cls, map, level):
        return super(Cluster, cls).__new__(cls, map, level['xPos'].value, level['zPos'].value)

    def __init__(self, map, level):
        super(Cluster, self).__init__()
        self.level = level
        assert self.position not in map
        map[self.position] = self
        print "Added cluster <%d, %d>" % self.position

    def _set_level(self, level):
        #print level.pretty_tree().encode('ascii', 'replace')
        self._level = level
        self.blocks = str(level["Blocks"].value)
        for c in self.blocks:
            self.map.new_mesh(ord(c));

    level = property(fget=lambda self: self._level, fset=_set_level)
