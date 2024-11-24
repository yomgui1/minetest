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

from euclid import Vector3, Matrix4
from math import pi, cos, sin, asin, radians, floor
from pygame import Rect
from time import time

import entity

class Player(object):
    """Define a player in the model.

    Contains player's physical and logical abstractions.
    A player is attached to a map.
    """

    ## Player state:
    #
    # unborn  : not located on a map (no physical representation)
    # dying    : on map, physical aspect but not usable/killable, only for few instants before unborn state
    # spawned : temporary state like dying, physical.
    # falling : physical, no solid block under player
    # walking : physical, moving using specific physics values.
    # flying  : physical, like walking with specific physics and falling state not tested (except forced).
    # idle    : physical, not any other states.
    #
    ## States transitions:
    #
    # unborn : spawned
    # dying   : unborn, spawned
    # spawned: unborn, dying, idle, falling, walking, flying
    # falling: unborn, dying, idle, walking, flying
    # walking: unborn, dying, idle, falling, flying
    # idle   : unborn, dying, falling, walking, flying
    #

    map = None                      # attached map
    position = Vector3()            # position of the player origin, located under its "feet"
    _direction = Vector3()          # look direction
    _sky = None                     # cached sky vector computed from rotations
    _move_req = Vector3()
    _rot = Matrix4()                # matrix describing the rotation
    _angle_x = 0.0
    _angle_y = 0.0
    _state = 'unborn'
    life = 20

    MAX_DIE_TIME = 3.0
    HURT_POINTS_SOLID = 2
    FALLING_VECTOR = Vector3(0,-1.0,0)
    WALK_SPEED = 0.2

    def __init__(self, name):
        self.name = name

    def enter_map(self, map):
        self.map = map
        self.spawn()

    def exit_map(self):
        self.map = None

    def signal(self, name, *args):
        pass

    def set_state(self, n):
        o = self._state
        if o != n:
            self._state = n
            self.signal("state", o, n)
            if n == 'dying':
                self.on_die()

    state = property(fset=set_state, fget=lambda self: self._state)

    @property
    def direction(self, _dir_base=Vector3(0,0,1)):
        if not self._direction:
            self._direction = (self._rot * _dir_base).normalize()
        return self._direction

    @property
    def sky(self, _sky_base=Vector3(0,1,0)):
        if not self._sky:
            self._sky = (self._rot * _sky_base).normalize()
        return self._sky

    def on_die(self):
        assert self._state == 'dying'
        self._die_time = time()

    def spawn(self):
        #base = Vector3(0,0,1)
        #dir = Vector3(*dir)
        #self._rot = self._rot.new_rotate_axis(base.angle(dir), base.cross(dir))
        #self._move_req = Vector3()
        self.state = 'spawned'

    def kill(self):
        self.state = 'unborn'

    def hurt(self, n):
        self.life -= n
        if self.life <= 0:
            self.state = 'dying'

    def update(self):
        st = self.state
        if st == 'walking':
            self.update_dynamics()
            self.check_position()
        elif st == 'flying':
            self.update_dynamics()
            self.check_position()
        elif st == 'falling':
            self.update_dynamics()
            self.check_position()
        elif st == 'idle':
            self.check_position()
        elif st == 'dying':
            self.update_dynamics()
            self.check_dead()
        elif st == 'spawned':
            self.state = 'idle'

    def check_dead(self):
        assert self._state == 'dying'
        if time() - self._die_time > self.MAX_DIE_TIME:
            self.kill()

    def _check_bounds(self, y, n):
        if n is None:
            if y <= -64:
                self.state = 'dying'
            else:
                self.hurt(self.HURT_POINTS_SOLID)
        return True

    def check_position(self):
        return
        x, y, z = map(lambda v: int(v+.5), self.position)
        n = self.map.get_block(x, y, z)
        if self._check_bounds(y, n):
            if entity.is_block_solid(n):
                if self._state == 'walking':
                    self._move_req += [0, 1, 0]
                else:
                    self.hurt(self.HURT_POINTS_SOLID)
            else:
                n = self.map.get_block(x, y-1, z)
                if n is not None:
                    if not entity.is_block_solid(n):
                        self.state = 'falling'
                        self._move_req = self.FALLING_VECTOR
                    elif self._state == 'falling':
                        self.state = 'idle'

    def update_dynamics(self):
        if self._move_req:
            # Compute new position, check for collisions
            pos = self.position + self._move_req
            #pos = self.map.clip_vector(*pos)

            # Update player internals
            self._move_req -= pos - self.position
            self.position = pos

    def request_walk_step(self, dir='forward'):
        if self._state in ('idle', 'walking', 'flying'):
            d = self.direction.copy()
            d.y = 0
            d.normalize()
            if dir == 'backward':
                self._move_req -= d * self.WALK_SPEED
            elif dir == 'left':
                self._move_req -= d.cross(self.sky) * self.WALK_SPEED
            elif dir == 'right':
                self._move_req += d.cross(self.sky) * self.WALK_SPEED
            else:
                self._move_req += d * self.WALK_SPEED
            self.state = 'walking'

    def request_fly_step(self):
        if self._state in ('idle', 'walking', 'flying'):
            self._move_req += direction
            if dir == 'backward':
                self._move_req -= self.direction * self.FLY_SPEED
            elif dir == 'left':
                self._move_req -= self.direction.cross(self.sky) * self.FLY_SPEED
            elif dir == 'right':
                self._move_req += self.direction.cross(self.sky) * self.FLY_SPEED
            else:
                self._move_req += self.direction * self.FLY_SPEED
            self.state = 'flying'

    def rotate(self, ry, rx):
        # Just modify the rotation matrix
        # direction and sky vectors computed on demands only
        ry = self._angle_y = self._angle_y + ry
        rx = self._angle_x = max(-pi/2.01, min(self._angle_x + rx, pi/2.01))
        self._rot = Matrix4().rotatey(ry).rotatex(rx)
        self._direction = None
        self._sky = None

    def setup_on_level(self, data):
        #self.position[:] = [x.value for x in data["Pos"].tags]
        #self.position[:] = (0,3,0)
        self.position[:] = (0,70,0)

class MainPlayer(Player):
    height = 2.0                    # Total height size
    cam_height = height - 0.2       # +y to add for camera position
