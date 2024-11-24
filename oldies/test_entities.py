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

import OpenGL

OpenGL.CONTEXT_CHECKING = True
OpenGL.STORE_POINTERS = True
#OpenGL.USE_ACCELERATE = False

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL import platform

import pygame
from pygame.locals import *

pygame.init()
pygame.display.set_mode((512,512), OPENGL | DOUBLEBUF)

# must be imported after set_mode to have a valid TGL context
from entity import EntityFactory, BlockFactory

glEnable(GL_TEXTURE_2D)
glShadeModel(GL_FLAT)
glClearDepth(1.)
glEnable(GL_DEPTH_TEST)
glDepthFunc(GL_LEQUAL)
glEnable(GL_ALPHA_TEST)
glAlphaFunc(GL_GREATER, 0)
glCullFace(GL_BACK)

glMatrixMode(GL_PROJECTION)
glLoadIdentity()
gluPerspective(60., 1.0, 1.0, 20.)
glMatrixMode(GL_MODELVIEW)
glLoadIdentity()
gluLookAt(0., 0., 6., 0., 0., 0., 0., 1., 0.)

glClearColor (0.0, 0.0, 0.0, 1.0)
glClearDepth(1.0)
glColor3f(1.0, 1.0, 1.0)

a = 0
rotx = 0
fac = 0.5

entities = [
    EntityFactory('human'),
    EntityFactory('skeleton'),
    EntityFactory('zombie'),
    EntityFactory('creeper'),
    EntityFactory('sheep'),
    EntityFactory('sheep_fur'),
    EntityFactory('pig'),
    BlockFactory('grass'),
    BlockFactory('brick'),
    BlockFactory('tnt'),
    BlockFactory('tree_leaf'),
    BlockFactory('tree_trunk'),
    ]

def draw(entity):
    global a, fac
    
    glClear( GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT )
    
    #glPushMatrix()
    glRotatef(-1, 0, 1, 0)
    glPushMatrix()
    glRotatef(rotx, 1, 0, 0)
    glTranslatef(0, -2., 0)
    glPushMatrix()
    entity.render()
    glPopMatrix()
    glPopMatrix()
    
    glFlush()

entity = 0
pygame.key.set_repeat(500,30)
while 1:
    event=pygame.event.poll()
    
    if event.type is QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
        break
    
    if event.type == KEYDOWN:
        if event.key == K_LEFT:
            entity = (entity - 1) % len(entities)
        if event.key == K_RIGHT:
            entity = (entity + 1) % len(entities)
        if event.key == K_UP:
            rotx = (rotx - 5) % 360
        if event.key == K_DOWN:
            rotx = (rotx + 5) % 360
            
    draw(entities[entity])
    
    pygame.display.flip()
    pygame.time.wait(10)

pygame.display.quit()
pygame.quit()
