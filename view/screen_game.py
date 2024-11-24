import pygame
import screen
import game

from math import sqrt, radians, asin

from model import entity
from euclid import Vector3
from threading import Lock
from OpenGL import GL
from OpenGL import GLUT

gui_text = """Game fps: %3.1f
Rendering time: %u ms
Camena Far: %u
Rendered faces: %u (%u/s)
Camera: (%.3f, %.3f, %.3f), (%.3f, %.3f, %.3f)"""

class GameScreen(screen.Screen):
    NAME =  'game'

    flat = 0
    show_stats = 1

    __lock = Lock()
    __hit_node = None
    _move = None
    r_faces = 0
    r_time = 0.0
    r_faces_per_sec = 0.0

    def __get_hit_node(self):
        self.__lock.acquire()
        node = self.__hit_node
        self.__lock.release()
        return node

    def __set_hit_node(self, node):
        self.__lock.acquire()
        self.__hit_node = node
        self.__lock.release()

    hit_node = property(fset=__set_hit_node, fget=__get_hit_node)

    def setup(self, map, camera):
        self.parent.set_mouse_lock(True)
        self.parent.center_mouse((x/2 for x in self.parent.surface.get_size()))
        self.map = map
        self.camera = camera
        self.player = camera.player

    def draw(self, gl, width, height):
        camera = self.camera
        map = self.map

        if map is not None and camera is not None:
            if entity.Mesh._texture:
                texid = entity.Mesh._texture.texid
            else:
                texid = -1
            map.lock()
            camera.lock()
            try:
                cam_pos = camera.position
                cam_dir = camera.direction
                camera.setup(self.flat)
                #gl.draw_sky(camera.position, camera.direction)

                hit_node = map.render(camera, texid)
                hit_node = None

            finally:
                map.release()
                camera.release()
        else:
            cam_pos = (0, 0, 0)
            cam_dir = (0, 0, 0)

        if self.r_time >= 2.0:
            self.r_faces_per_sec = self.r_faces / self.r_time
            self.r_time = 0.0
            self.r_faces = 0
        else:
            self.r_time += map.rendering_time
            self.r_faces += map.drawn_faces

        # Enter in GUI mode
        gl.enter_2d(width, height)
        try:
            gl.set_color_rgb(1, 0, 0)
            gl.draw_cursor(9) # must be odd for a correct display

            # Display stats
            if self.show_stats:
                clock = self.parent.clock
                if 1:
                    gl.set_color_rgba(0, 0, 0, .5)
                    gl.draw_rect(0, height-25*7-5, width-1, 25*7+5)

                    gl.set_color_rgb(1,1,1)
                    gl.text(0, height-20, gui_text % ((clock.get_fps(), map.rendering_time*1000, camera.far,
                            map.drawn_faces, self.r_faces_per_sec) + cam_pos + cam_dir))
                else:
                    gl.set_color_rgba(0,0,0,.5)
                    GL.glRectf(0, 0, width-1, 20)
                    gl.set_color_rgb(1,1,1)

                    if hit_node:
                        gl.text(0, 0, "FPS: %3.1f, Range=%u, Selection=%d <%d,%d,%d>" % ((clock.get_fps(), camera.far, hit_node.id) + hit_node.position))
                    else:
                        gl.text(0, 0, "FPS=%3.1f, Rg=%u, F:%u <%.2f,%.2f,%.2f>" % ((clock.get_fps(), camera.far, map.drawn_faces) + cam_pos))
        finally:
            gl.leave_2d()

    def on_tick(self, ctrl):
        # Step into life cycle
        ctrl.update_map()

        if self._move:
            self._move()

    def on_mouse_motion(self, event):
        self.parent.center_mouse((x/2 for x in self.parent.surface.get_size()))

        dx, dy = event.rel

        player = self.player
        if player:
            player.rotate(-radians(dx/4.), radians(dy/4.))

    def on_key_down(self, event):
        key = event.key
        if key == pygame.K_ESCAPE:
            self.parent.quit()
            return True
        elif key == pygame.K_SPACE:
            self.parent.toggle_mouse_lock()
        elif key == pygame.K_3:
            self.flat = not self.flat
        elif key == pygame.K_f:
            self.map.toggle_fog()
        elif key in (pygame.K_KP_PLUS, 43):
            self.camera.far += 10
        elif key in (pygame.K_KP_MINUS, 45):
            self.camera.far -= 10
        elif key == pygame.K_p:
            print self.camera.position, self.camera.direction
        elif key == pygame.K_UP:
            self._move = lambda: self.player.request_walk_step('forward')
            self._move()
            self._move_key = key
        elif key == pygame.K_DOWN:
            self._move = lambda: self.player.request_walk_step('backward')
            self._move()
            self._move_key = key
        elif key == pygame.K_LEFT:
            self._move = lambda: self.player.request_walk_step('left')
            self._move()
            self._move_key = key
        elif key == pygame.K_RIGHT:
            self._move = lambda: self.player.request_walk_step('right')
            self._move()
            self._move_key = key
        elif key == pygame.K_s:
            self.show_stats = not self.show_stats

    def on_key_up(self, event):
        key = event.key
        if self._move and key == self._move_key:
            self._move = None

    def render_cluster_map(self, gl, map, camera, width, height):
        gl.set_color_rgba(0, 0, 0, .5)
        GL.glRectf(0, 0, 128, 128)
        gl.set_color_rgba(1, 0, 0, .5)
        cx = camera.px
        cz = camera.pz
        for cluster in map.itervalues():
            if cluster.render:
                x = 64 + cluster.x - cx
                y = 64 + cluster.z - cz
                GL.glRectf(x-8, y-8, x+7, y+7)
