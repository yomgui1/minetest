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
import sys
import lowlevel
import entity
import random
import game

from mvc import QueuedSet
from threading import RLock
from math import hypot
from itertools import izip

import mcr


class Map(lowlevel.Map):
    players = QueuedSet()
    main_player_spawn_position = None

    DEFAULT = None
    missings = set()

    die_level = -64

    main_player_spawn_pose = [(0, 80, 0), (0, 0, 1)]

    def __init__(self, *args, **kwds):
        super(Map, self).__init__(*args, **kwds)
        self._lock = RLock()

    def lock(self):
        self._lock.acquire()

    def release(self):
        self._lock.release()

    def new_mesh(self, idx):
        if self.has_mesh(idx): return
        mesh = self.get_mesh(idx)
        self.set_mesh(idx, mesh)

    def get_mesh(self, idx):
        if self.has_mesh(idx):
            return super(Map, self).get_mesh(idx)

        mesh = entity.MeshFactory(idx)
        if mesh is not None:
            return mesh

        Map.missings.add(idx)
        if Map.DEFAULT is None:
            Map.DEFAULT = entity.MeshFactory(46)

        return Map.DEFAULT

    def set_root(self, root):
        self.leveldat = mcr.LevelDat(os.path.join(root, "level.dat"))
        self.mcr = mcr.MCR(os.path.join(root, "region"))
        self.get_cluster_level = self.mcr.get_cluster_level

    #####################
    ## Players handling

    @property
    def player_data(self):
        return self.leveldat["Player"]

    def get_player_spawn_data(self):
        spawn = self.leveldat["SpawnX"].value, self.leveldat["SpawnY"].value, self.leveldat["SpawnZ"].value
        return spawn, (-1, 0, -1)

    def add_player(self, player):
        self.players.add(player)
        player.enter_map(self)

    def remove_player(self, player):
        self.players.remove(player)
        player.exit_map()

    def update(self):
        for player in self.players:
            player.update()

    def toggle_fog(self):
        self.lock()
        self.fog_enabled = not self.fog_enabled
        self.release()

    #####################
    ## Tests

    def test_flat(self):
        dist = 256
        for cx in xrange(dist):
            for cz in xrange(dist):
                self.add_face(self.get_mesh(2), 1, cx, 0, cz)

    def test_alpha(self):
        self.new_mesh(9)
        # general alpha rendering
        for x in range(3):
            for z in range(3):
                for y in range(3):
                    self.set_blockid(9,x,70+y, z)

    def test_alpha2(self):
        self.new_mesh(8)
        self.new_mesh(9)
        self.new_mesh(2)
        # general alpha rendering
        for x in range(3):
            for z in range(3):
                for y in range(3):
                    self.set_blockid(9,x,70+y, z)
        # test alpha between 2 clusters limits
        for x in range(8):
            for z in range(8):
                self.set_blockid(2,12+x,64, 12+z)
                for y in range(8):
                    self.set_blockid(8,12+x,65+y, 12+z)

    def test_occlusion(self):
        self.new_mesh(89)
        self.new_mesh(1)
        for x in range(3):
            self.set_blockid(89,1,x+70,0)
            self.set_blockid(1,3,x+70,0)

    def test_render(self):
        self.new_mesh(1)
        self.set_blockid(1, 2, 72, 2)
        self.set_blockid(1, 1, 72, 2)
        self.set_blockid(1, 3, 72, 2)
        self.set_blockid(1, 2, 72, 1)
        self.set_blockid(1, 2, 72, 3)
        self.set_blockid(1, 2, 71, 2)
        self.set_blockid(1, 2, 73, 2)
        for x in range(3):
            for z in range(3):
                self.set_blockid(1,x+12,72,z+10)

    def test_map(self):
        print "\n*** Testing tesselator"

        rx = 0
        rz = 0

        for cx in xrange(0,6):
            for cz in xrange(0,6):
                try:
                    level = self.get_cluster_level((rx << 9) + cx*16 - 128,
                                                   (rz << 9) + cz*16 - 128)
                except KeyError:
                    pass
                else:
                    blocks = level['Blocks'].value
                    for i, c in enumerate(blocks):
                        self.new_mesh(c)
                    self.add_blocks(blocks, cx, cz)
