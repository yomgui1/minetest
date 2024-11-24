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
import pygame
import os
import renders
import gl as _gl

import screen_welcome
import screen_game

import game

from euclid import Plane, Point3, Vector3
from threading import Thread, Event

GAME_FPS = 30

class RenderMediator(mvc.Mediator):
    pass


class PyGameDisplay(object):
    NORMAL_TOP    = Vector3(0, 1, 0)
    NORMAL_BOTTOM = Vector3(0, -1, 0)
    NORMAL_LEFT   = Vector3(-1, 0, 0)
    NORMAL_RIGHT  = Vector3(1, 0, 0)
    NORMAL_FRONT  = Vector3(0, 0, 1)
    NORMAL_REAR   = Vector3(0, 0, -1)
    
    map = None      # Map
    camera = None   # Camera
    mouse_lock = False
    flat = 0
    
    def _render(self, gl, *size):
        gl.clear()
        self.screen.draw(gl, *size)
        pygame.display.flip()
        
    def __kill_render(self):
        if self._render_loop.isSet():
            print 'killing render thread...'
            self._render_loop.clear()
            self._render_trig.set()
            self._render_thread.join()
        
    def __del__(self):
        pass
    
    def init(self):
        pygame.init()
        renders.load_renders()
        
        _pre_display_init()
        pygame.display.set_mode((game.Game.options.width,
                                 game.Game.options.height),
                                pygame.OPENGL | pygame.DOUBLEBUF)
        _post_display_init()
        
        self.surface = pygame.display.get_surface()

        #pygame.key.set_repeat(500,30)
        self.set_caption("Test")
        
        self.clock = pygame.time.Clock()
        
        # Setup the render job
        self._render_trig = Event()
        self._render_loop = Event()
        self._render_loop.set()
        self.gl = _gl.GUIOpenGL(self.surface)
        #self._render_thread = Thread(target=self._render_job,
        #                             args=(self._render_loop,
        #                                   self._render_trig,
        #                                   gl))
    
    def use_screen(self, name, *args, **kwds):
        self.screen = screen.get_screen(name, self, *args, **kwds)
    
    def set_caption(self, text):
        pygame.display.set_caption(text)
        
    def mainloop(self, tick):
        self.running = True
        clock = self.clock
        #self.use_screen('welcome')
        self.go()
        #self._events_thread.start()
        while self.running:
            self._render(self.gl, *self.surface.get_size())
            clock.tick(GAME_FPS)
            tick.emit()
            
    def quit(self, *args):
        self.running = False
        self.map = self.camera = None

    def go(self):
        self.use_screen('game', self.map, self.camera)
        self.ctrl.start_game_mode()

    def update(self):
        self._render_trig.set() # request remote rendering
        
    def center_mouse(self, pos, f1=pygame.event.set_blocked, f2=pygame.event.set_allowed, f3=pygame.mouse.set_pos):
        if self.mouse_lock:
            f1(pygame.MOUSEMOTION)
            f3(*pos)
            f2(pygame.MOUSEMOTION)

    def set_mouse_lock(self, state=True):
        self.mouse_lock = state
        
        pygame.mouse.set_visible(not state)
        
        if state:
            pygame.event.set_allowed(pygame.MOUSEMOTION)
        else:
            pygame.event.set_blocked(pygame.MOUSEMOTION)

    def toggle_mouse_lock(self):
        self.set_mouse_lock(not self.mouse_lock)
    
    def action_at_selection(self):
        node = self.hit_node
        if self.get_hit_normal() is self.NORMAL_TOP:
            pos = map(int, node.position)
            pos[1] += 1
            
            if self.map.get_node(*pos) is None:
                # Create a new cube in direction of hit normal
                self.map.add_cube(self.block_list[self.current], *pos)
        elif node:
            pos = map(int, node.position)
            self.map.remove_cube(*pos)

    def on_mouse_motion(self, event):
        self.screen.on_mouse_motion(event)
        
    def on_mouse_button_down(self, event):
        self.screen.on_mouse_button_down(event)
        
    def on_mouse_button_up(self, event):
        self.screen.on_mouse_button_up(event)

    def on_key_down(self, event):
        self.screen.on_key_down(event)
        
    def on_key_up(self, event):
        self.screen.on_key_up(event)


class PyGameDisplayMediator(mvc.Mediator):
    NAME = "PyGameDisplay"

    def on_register(self):
        ctrl = self.ctrl = self.facade.controller
        comp = self.component
        comp.ctrl = ctrl
        
        ctrl.init_signal.register(comp.init)
        ctrl.tick_signal.register(self.on_tick)
        ctrl.quit_signal.register(comp.quit)
        
        ctrl.keydown_signal.register(comp.on_key_down)
        ctrl.keyup_signal.register(comp.on_key_up)
        ctrl.mousemotion_signal.register(comp.on_mouse_motion)
        ctrl.mousebuttondown_signal.register(comp.on_mouse_button_down)
        ctrl.mousebuttonup_signal.register(comp.on_mouse_button_up)
    
    def run(self):
        self.component.mainloop(self.ctrl.tick_signal)
        
    def use_map(self, map_proxy):
        self.component.map = map_proxy.component
        
    def attach_camera(self, camera_proxy):
        self.component.camera = camera_proxy.component
        
    def on_tick(self):
        ctrl = self.ctrl
        
        try:
            # Handle user inputs
            ctrl.handler_input_events()
            
            self.component.screen.on_tick(ctrl)
        
            # Redraw the view
            self.component.update()
        except Exception, e:
            print "exception:", e

def _pre_display_init(): pass
def _post_display_init(): pass

###
## Platforms stuffs

if os.name == 'morphos':
    from platforms.morphos import _post_display_init
