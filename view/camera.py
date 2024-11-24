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

import mvc
import lowlevel

from euclid import Vector3, Point3, Ray3
from math import radians
from threading import RLock

class Camera(lowlevel.Camera):
    """Used to render the Map into the view.
    Can be attached to a player, in this case camera movements are linked to this player.
    If no player attached, the camera is in fly mode (default).
    """

    def __init__(self, player=None):
        lowlevel.Camera.__init__(self)
        self._lock = RLock()
        self.far = 70
        self.fov = radians(90)
        self.position = (0.0, 1.6, 0.0)
        self.set_player(player)

    def lock(self):
        self._lock.acquire()

    def release(self):
        self._lock.release()

    def move(self, *args):
        self._lock.acquire()
        self.position = args
        self._lock.release()

        # Refresh OpenGL matrices
        self.update()

    def sync(self, pos, dir, sky):
        self._lock.acquire()
        self.position = tuple(pos)
        self.direction = tuple(dir)
        self.sky = tuple(sky)
        self._lock.release()

        # Refresh OpenGL matrices
        self.update()

    def set_player(self, player):
        self.player = player
        if player:
            self.sync(player.position, player.direction, player.sky)

    def get_ray(self):
        self._lock.acquire()
        ray = Ray3(Point3(*self.position), Vector3(*self.direction))
        self._lock.release()
        return ray

class CameraMediator(mvc.Mediator):
    NAME = 'Camera'

    def enable(self):
        #self.facade.controller.mousemotion_signal.register(self.on_mouse_motion)
        self.facade.controller.tick_signal.register(self.on_tick)

    def disable(self):
        #self.facade.controller.mousemotion_signal.unregister(self.on_mouse_motion)
        self.facade.controller.tick_signal.unregister(self.on_tick)

    def on_tick(self):
        cam = self.component
        player = cam.player

        pos = player.position.copy()
        pos.y += player.cam_height # setup it before the sync or camera's internal states are not updated correctly

        cam.sync(pos, player.direction, player.sky)
