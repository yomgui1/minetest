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

from __future__ import with_statement

import sys
import os
import gzip
import zlib

from struct import unpack_from, unpack
from pprint import pprint
from cStringIO import StringIO
from nbt.nbt import NBTFile

class MCR(object):
    """MCR cache class.

    MCR instance try to find region file that contains a position and cache data.
    This class handles data uncompressing and cluster data fetching.
    """

    MAX_CLUSTERS = 1024 # Choose to fully load one region

    def __init__(self, pathname):
        self._root = pathname
        self._level_cache = {}
        self.flush()

    def flush(self):
        self._region_rx = None
        self._region_rz = None
        self._region_locations = None
        self._region_timestamps = None
        self._region_filename = None
        self._level_cache.clear()
        self._pos_order = []

    def get_cluster_level(self, x, z):
        """Return an NBT object with cluster data for the given position.

        Handles region finding, data uncompressing and cache.
        """

        x = int(x); z = int(z)
        pos = x >> 4, z >> 4

        # Check already loaded cluster cache first
        level = self._level_cache.get(pos, None)
        if level is None:
            # load suitable region (and cache), raise error if not found
            # Todo: create a new region file if nothing found
            self.use_region(x >> 9, z >> 9)
            level = self._level_cache[pos]

        try:
            self._pos_order.remove(pos)
        except:
            pass
        self._pos_order.append(pos)
        return level

    def use_region(self, rx, rz):
        if rx != self._region_rx or rz != self._region_rz:
            self._region_filename = os.path.join(self._root, "r.%d.%d.mcr" % (rx, rz))
            print "Loading file '%s'" % self._region_filename

            with open(self._region_filename, 'rb') as fd:
                # read 8kib header
                locations = fd.read(4096)
                timestamps = fd.read(4096)

                # decode clusters data positions and offsets
                for offset in xrange(0, 4096, 4):
                    value = unpack_from(">I", locations, offset)[0]
                    chunk_offset = value >> 8
                    count = value & 0xff
                    # UNUSED: ts = unpack_from(">I", timestamps, offset)[0]

                    # empty chunk
                    if chunk_offset == 0 and count == 0:
                        continue

                    if chunk_offset < 2 or count == 0:
                        print UserWarning("Invalid cluster location data: offset=%u, count=%u" % (chunk_offset, count))
                        continue

                    # Unpack chunk data
                    fd.seek(4096*chunk_offset)
                    level = self.unpack_level(fd)

                    # Cache level
                    pos = level['xPos'].value, level['zPos'].value
                    self._level_cache[pos] = level
                    try:
                        self._pos_order.remove(pos)
                    except:
                        pass
                    self._pos_order.append(pos)
                    if len(self._pos_order) > MCR.MAX_CLUSTERS:
                        self._pos_order.pop(0)
                    #print "\rLoaded level %4u" % (offset/4),
                    #sys.stdout.flush()
            print "Done"

    def unpack_level(self, fd):
        length, compression = unpack(">IB", fd.read(5))

        if length == 0:
            print UserWarning("Chunk has a zero data length!")
            return

        if compression not in [1, 2]:
            print UserWarning("Chunk has unknown compression method (%u)!" % (compression))
            return

        # Read compressed chunk data
        n = length - 1 # max should be 1MB
        rawdata = fd.read(n)

        if compression == 1:
            nbt = NBTFile(fileobj=StringIO(rawdata))
        else:
            nbt = NBTFile(buffer=StringIO(zlib.decompress(rawdata)))

        return nbt['Level']

    def __contains__(self, pos):
        return pos in self._pos_order


class LevelDat(object):
    def __init__(self, filename):
        print "Loading file '%s'" % filename
        nbt = NBTFile(filename)
        self._data = nbt["Data"]
        #print self._data.pretty_tree()

    def __getitem__(self, name):
        return self._data[name]
