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

import pygame
import screen
import gui

from OpenGL import GL

class WelcomeScreen(screen.Default2DScreen):
    NAME =  'welcome'

    action = 'enter'

    def draw_2d(self, gl, width, height):
        w = 200
        left = (width - w) / 2
        
        GL.glPushMatrix()
        GL.glScalef(4, 4, 1)
        GL.glRotatef(30, 0, 0, 1)
        gui.Text.draw(gl, "Crafton", 50, height/2+30, color=(1,1,0,1))
        GL.glPopMatrix()
        
        left, top, w, h = gui.Button.draw(gl, 'Enter', left, height/2+50, w, 0)
        if self.is_inside(self.mx, height-self.my-1, left, top, w, h) or self.action == 'enter':
            gl.set_color_rgba(1,0,0,0.33)
            gl.draw_rect(left, top-h+1, w, h, 1)
            self.action = 'enter'
            
        left, top, w, h = gui.Button.draw(gl, 'Quit', left, top-h-5, w, h)
        if self.is_inside(self.mx, height-self.my-1, left, top, w, h) or self.action == 'quit':
            gl.set_color_rgba(1,0,0,0.33)
            gl.draw_rect(left, top-h+1, w, h, 1)
            self.action = 'quit'
            
    def do_action(self):
        if self.action == 'quit':
            self.parent.quit()
        elif self.action == 'enter':
            self.parent.go()
        
    def on_mouse_button_down(self, event):
        if event.button == 1:
            self.do_action()
                
    def on_key_down(self, event):
        key = event.key
        if key == pygame.K_ESCAPE:
            self.parent.quit()
            return True
        elif key == pygame.K_RETURN:
            self.do_action()
