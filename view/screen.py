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
import texture

class _MetaScreen(type):
    __all_classes = {}
    __all_screens = {}

    def __init__(cls, name, bases, dct):
        type.__init__(cls, name, bases, dct)
        if 'NAME' in dct:
            _MetaScreen.__all_classes[dct['NAME']] = cls

    @staticmethod
    def get_screen(name, parent):
        screen = _MetaScreen.__all_screens.get(name)
        if screen is None:
            screen = _MetaScreen.__all_classes[name](parent)
            _MetaScreen.__all_screens[name] = screen
        return screen

class Screen(object):
    __metaclass__ = _MetaScreen

    __current = None

    def __init__(self, parent):
        self.parent = parent

    def setup(self, *args, **kwds): pass

    def cleanup(self): pass

    @mvc.virtualmethod
    def draw(self, gl, width, height): pass

    @staticmethod
    def get_screen(name, parent, *args, **kwds):
        "Create requested screen if not existing yet or return existing one"
        if Screen.__current is not None:
            Screen.__current.cleanup()
        Screen.__current = screen = _MetaScreen.get_screen(name, parent)
        screen.setup(*args, **kwds)
        return screen

    def on_mouse_motion(self, event):
        self.mx, self.my = event.pos

    def on_mouse_button_up(self, event): pass
    def on_mouse_button_down(self, event): pass
    def on_key_down(self, event): pass
    def on_key_up(self, event): pass

    def on_tick(self, ctrl): pass

    @staticmethod
    def is_inside(x, y, left, top, width, height):
        return x >= left and x < left+width and y <= top and y > top - height

get_screen = Screen.get_screen

class Default2DScreen(Screen):
    bg_tex = None
    mx = -1
    my = -1

    def setup(self):
        # Texture from http://www.freeseamlesstextures.com/
        self.bg_tex = texture.GLTexture('data/welcome_bg.png', tile=True)

    def cleanup(self):
        self.bg_tex.cleanup()
        self.bg_tex = None

    def draw(self, gl, width, height):
        gl.enter_2d(width, height)
        try:
            n = 256./width * 10
            gl.draw_rect_tex(0, 0, width, height, self.bg_tex, 0, 0, n, n)
            self.draw_2d(gl, width, height)
        finally:
            gl.leave_2d()

    @mvc.virtualmethod
    def draw_2d(self, gl, width, height): pass
