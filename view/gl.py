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

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import glFreeType
import math
import pygame

from texture import GLTexture

global texture
texture = None


class GUIOpenGL(object):
    def __init__(self, surface):
        # On MorphOS the TGL context from the pygame display must be valid
        # before any GL APi calls.
        # And in anycases, the surface must be an OpenGL one!
        assert surface.get_flags() & pygame.OPENGL
        self.surface = surface

        #glutInit()

        # Font for printing
        self.font = glFreeType.font_data("view/Test.ttf", 15)
        self.glyph_advance = 14
        self.glyph_height = self.font.m_font_height*1.1

        # And setup a default OpenGL state
        self.default_state()

    def quit(self):
        if self.font:
            self.font.release()
            self.font = None

    def __del__(self):
        self.quit()

    def default_state(self):
        glShadeModel(GL_FLAT)
        glClearColor(1.0, 1.0, 1.0, 1.0)
        glClearDepth(1.0)
        glColor3f(0.0, 1.0, 0.0)

        glEnable(GL_DEPTH_TEST)
        glDepthFunc(GL_LEQUAL)

        glEnable(GL_ALPHA_TEST)
        glAlphaFunc(GL_GREATER, 0)

        glCullFace(GL_BACK)
        glFrontFace(GL_CCW)
        glEnable(GL_CULL_FACE)

        glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)
        ##glHint(GL_LINE_SMOOTH_HINT, GL_FASTEST);

    def enter_2d(self, width, height):
        self.width = width
        self.height = height

        glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT | GL_TRANSFORM_BIT)

        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        self.fac = float(self.width) / self.height
        glOrtho(0, width-1, 0, height-1, -10, 10)

        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

        glTranslatef(0.375, 0.375, 0)

        glShadeModel(GL_FLAT)
        glDisable(GL_DEPTH_TEST)
        glDisable(GL_TEXTURE_2D)
        glEnable(GL_BLEND)

    def leave_2d(self):
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)
        glPopAttrib()

    def clear(self):
        # Clear display
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def draw_cube(self, cube):
        self.width, self.height = self.surface.get_size()
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        glOrtho(0, self.width, 0, self.height, -100, 100)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        gluLookAt(0, 0, -1, 0, 0, 0, 0, 1, 0)
        glTranslatef(40-self.width, 40, 0)
        glRotatef(-45, 1, 0, 0)
        glRotatef(45, 0, 1, 0)
        glScalef(30, 30, 30)
        glColor3f(1,1,1)
        glLineWidth(2.0)
        glDisable(GL_DEPTH_TEST)
        glutWireCube(1.0)
        glEnable(GL_DEPTH_TEST)
        glLineWidth(1.0)
        #cube.render()

    set_color_rgb = glColor3f
    set_color_rgba = glColor4f

    def text(self, x, y, text):
        return self.font.glPrint(x, y, text)

    def get_text_size(self, text):
        return self.glyph_advance*len(text), self.glyph_height*len(text.split('\n'))

    def draw_rect_tex(self, x, y, w, h, texid, tx, ty, tw, th):
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texid)

        glColor3f(1, 1, 1)
        glBegin(GL_QUADS)
        glTexCoord2f(tx   , ty   ); glVertex2f(x  , y  )
        glTexCoord2f(tx   , ty+th); glVertex2f(x  , y+h)
        glTexCoord2f(tx+tw, ty+th); glVertex2f(x+w, y+h)
        glTexCoord2f(tx+tw   , ty); glVertex2f(x+w, y)
        glEnd()

        glDisable(GL_TEXTURE_2D)

    def draw_rect(self, x, y, w, h, filled=1, size=1.0):
        if not filled:
            glPolygonMode(GL_FRONT, GL_LINE)
        glLineWidth(size)
        glRectf(x,y,x+w,y+h)
        if not filled:
            glPolygonMode(GL_FRONT, GL_FILL)
        glLineWidth(1.0)

    def draw_cursor_square(self):
        cx = self.width / 2.
        cy = self.height / 2.

        glColor3f(1, 1, 1)

        glBegin(GL_LINES)
        glVertex2f(cx-10,cy+5)
        glVertex2f(cx-10,cy+10)

        glVertex2f(cx-10,cy+10)
        glVertex2f(cx-5,cy+10)

        glVertex2f(cx+5,cy+10)
        glVertex2f(cx+10,cy+10)

        glVertex2f(cx+10,cy+10)
        glVertex2f(cx+10,cy+5)

        glVertex2f(cx+10,cy-5)
        glVertex2f(cx+10,cy-10)

        glVertex2f(cx+10,cy-10)
        glVertex2f(cx+5,cy-10)

        glVertex2f(cx-5,cy-10)
        glVertex2f(cx-10,cy-10)

        glVertex2f(cx-10,cy-10)
        glVertex2f(cx-10,cy-5)
        glEnd

    _cursor_list = None
    def draw_cursor(self, size):
        if self._cursor_list is None:
            self._cursor_list = glGenLists(1)
            glNewList(self._cursor_list, GL_COMPILE)

            glBegin(GL_LINES)
            glVertex3f(0,.5,0)
            glVertex3f(0,-.5,0)
            glVertex3f(-.5,0,0)
            glVertex3f(.5,0,0)
            glEnd()

            glEndList()

        cx = self.width / 2
        cy = self.height / 2

        glPushMatrix()
        glTranslatef(cx, cy, 0)
        glScalef(size, size, 0)
        glCallList(self._cursor_list)
        glPopMatrix()

    def draw_add_sign(self, x, y, z):
        glPushAttrib(GL_ENABLE_BIT | GL_CURRENT_BIT)
        glPushMatrix()

        glDisable(GL_TEXTURE_2D)
        glEnable(GL_CULL_FACE)

        glColor3f(0, 0, 0)
        glTranslatef(x,y,z)
        glutWireCube(1.01)

        glPopMatrix()
        glPopAttrib()

    _skylist = None
    def draw_sky(self, pos, dir):
        if self._skylist is None:
            self._skylist = glGenLists(1)
            glNewList(self._skylist, GL_COMPILE)

            # Render the front quad

            glBegin(GL_QUADS)
            glColor3f(140/255.,186/255.,250/255.); glVertex3f(  0.5, 0, -0.5 )
            glColor3f(140/255.,186/255.,250/255.); glVertex3f( -0.5, 0, -0.5 )
            glColor3f(140/255.,186/255.,250/255.); glVertex3f( -0.5,  0.5, -0.5 )
            glColor3f(140/255.,186/255.,250/255.); glVertex3f(  0.5,  0.5, -0.5 )
            glEnd()

            # Render the left quad

            glBegin(GL_QUADS)
            glColor3f(140/255.,186/255.,250/255.); glVertex3f(  0.5, 0,  0.5 )
            glColor3f(140/255.,186/255.,250/255.); glVertex3f(  0.5, 0, -0.5 )
            glColor3f(140/255.,186/255.,250/255.); glVertex3f(  0.5,  0.5, -0.5 )
            glColor3f(140/255.,186/255.,250/255.); glVertex3f(  0.5,  0.5,  0.5 )
            glEnd()

            # Render the back quad

            glBegin(GL_QUADS)
            glColor3f(140/255.,186/255.,250/255.); glVertex3f( -0.5, 0,  0.5 )
            glColor3f(140/255.,186/255.,250/255.); glVertex3f(  0.5, 0,  0.5 )
            glColor3f(140/255.,186/255.,250/255.); glVertex3f(  0.5,  0.5,  0.5 )
            glColor3f(140/255.,186/255.,250/255.); glVertex3f( -0.5,  0.5,  0.5 )
            glEnd()

            # Render the right quad

            glBegin(GL_QUADS)
            glColor3f(140/255.,186/255.,250/255.); glVertex3f( -0.5, 0, -0.5 )
            glColor3f(140/255.,186/255.,250/255.); glVertex3f( -0.5, 0,  0.5 )
            glColor3f(140/255.,186/255.,250/255.); glVertex3f( -0.5,  0.5,  0.5 )
            glColor3f(140/255.,186/255.,250/255.); glVertex3f( -0.5,  0.5, -0.5 )
            glEnd()

            # Render the bottom quad
            glColor3f(0, 0, 0)

            glBegin(GL_QUADS)
            glVertex3f( -0.5, 0, -0.5 )
            glVertex3f(  0.5, 0, -0.5 )
            glVertex3f(  0.5, 0,  0.5 )
            glVertex3f( -0.5, 0,  0.5 )
            glEnd()

            # Render the top quad
            glColor3f(140/255.,186/255.,250/255.)

            glBegin(GL_QUADS)
            glVertex3f( -0.5,  0.5, -0.5 )
            glVertex3f( -0.5,  0.5,  0.5 )
            glVertex3f(  0.5,  0.5,  0.5 )
            glVertex3f(  0.5,  0.5, -0.5 )
            glEnd()

            glEndList()

        glPushAttrib(GL_ENABLE_BIT)
        glDisable(GL_DEPTH_TEST)
        glPushMatrix()
        glLoadIdentity()
        gluLookAt(0, 0, 0, dir[0], dir[1], dir[2], 0, 1, 0)
        glCallList(self._skylist)
        glPopMatrix()
        glPopAttrib()
