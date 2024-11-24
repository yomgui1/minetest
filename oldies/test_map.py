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
from pygame.locals import *

import OpenGL

from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *

import sys
import os
import math
import random

import entity
import lowlevel

from camera import Camera
from map import Map
from texture import GLTexture

def gen_map(max_level=3, r=50, randomize=True):
    map = Map()
    samples = []
    print "Generating map...".ljust(60)
    for l in xrange(max_level):
        for cy in xrange(-r, r+1):
            for cx in xrange(-r, r+1):
                if math.hypot(cx, cy) < (r-l):
                    node = map.add_cube('earth', cx, l, cy)
                    x = node.cube.x
                    y = node.cube.y
                    z = node.cube.z
                    assert cx == x and l == y and cy == z
                    assert node[x,y,z] is node
                    
                    if l == max_level-1:
                        samples.append((cx, cy))
            print "\rlevel %u: [%-25s]" % (l, '='*((cy+r)*25/(r*2))+'>'),
            sys.stdout.flush()
                
    if randomize:
        print "\rAdd some random...".ljust(60)
        for cx, cy in random.sample(samples, int(len(samples) * 0.1)):
            map.add_cube('grass', cx, max_level, cy)

    return map
    
def gen_ao_test_map():
    map = Map()
    samples = []
    print "Generating map...".ljust(60)
    for cx in xrange(-10, 11):
        for cz in xrange(-10, 11):
            map.add_cube('grass', cx, 0, cz)
            
    #map.add_cube('grass', 0, 1, 0)
    #map.add_cube('grass', -2, 1, -2)
    #map.add_cube('grass', -2, 1, 2)
    #map.add_cube('grass', 2, 1, -2)
    
    #for i in xrange(3):
    #    map.add_cube('grass', 2, 1+i, 2)
    #    map.add_cube('grass', 1, 1+i, 3)
    #    map.add_cube('grass', 3, 1+i, 1)
    #    map.add_cube('grass', 3, 1+i, 3)
    return map

def map_from_png(filename):
    map = Map()
    
    imgsurf = pygame.image.load(filename)
    imgstring = pygame.image.tostring(imgsurf, "RGBA", 1)
    width, height = imgsurf.get_size()
    
    cx = int(width / 2)
    cy = int(height / 2)
    
    print "Generating map...".ljust(60)
    for y in xrange(height):
        for x in xrange(64):
            i = (y*width + x) * 4
            level = sum(ord(c) for c in imgstring[i:i+3]) / 3
            level = int((level/255.)**2 * 8)
            px = x - cx
            pz = y - cy
            for n in xrange(0, level):
                map.add_cube('earth', px, n, pz)
            map.add_cube('grass', px, level, pz)
            
        print "\r[%-25s]" % ('='*(y*25/height)+'>'),
        sys.stdout.flush()
    print '\r'.ljust(60)

    return map
        
def gl_init(cam_fov):
    #glShadeModel(GL_SMOOTH)
    glShadeModel(GL_FLAT)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_AUTO_NORMAL)
    glEnable(GL_NORMALIZE)
    glDepthFunc(GL_LEQUAL)
    glAlphaFunc(GL_GREATER, 0)
    
    glEnable(GL_TEXTURE_2D)
    
    glCullFace(GL_BACK)
    glDisable(GL_CULL_FACE)
    
    glHint(GL_PERSPECTIVE_CORRECTION_HINT, GL_NICEST)

    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(math.degrees(cam_fov) / 2, 1.0, .5, 10000.)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glClearColor(1.0, 1.0, 1.0, 1.0)
    glClearDepth(1.0)
    glColor3f(1.0, 1.0, 1.0) # For testing

class Player(object):
    state = None
    speed = 0.5
    step_fw = 0.0
    
    def __init__(self):
        pass
    
    def forward(self):
        self.step_fw = self.speed
        
    def stop(self):
        self.step_fw = 0.0
        
    def update(self):
        if self.step_fw > 0.0:
            self.camera.forward(self.step_fw)
            
        pygame.event.pump()

class Sky(object):
    def __init__(self):
        self._texture = GLTexture("data/clouds.png", sky=True)
        
    def render(self):
        glDisable(GL_LIGHTING)
        glDisable(GL_CULL_FACE)
        
        glTexGeni(GL_S, GL_TEXTURE_GEN_MODE, GL_SPHERE_MAP)
        glTexGeni(GL_T, GL_TEXTURE_GEN_MODE, GL_SPHERE_MAP)
        glEnable(GL_TEXTURE_GEN_S)
        glEnable(GL_TEXTURE_GEN_T)
        
        glMatrixMode(GL_TEXTURE)
        glScale(1000, 1000, 1000)
        glBindTexture(GL_TEXTURE_2D, self._texture.texid)
        glLoadIdentity()
        glMatrixMode(GL_MODELVIEW)
        
        glEnable(GL_ALPHA_TEST)
        glutSolidSphere(1000, 32, 32)
        glDisable(GL_ALPHA_TEST)
        
        glDisable(GL_TEXTURE_GEN_S)
        glDisable(GL_TEXTURE_GEN_T)

def pushScreenCoordinateMatrix():
    glPushAttrib(GL_TRANSFORM_BIT)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 0, 512, 512)
    glPopAttrib()

def pop_projection_matrix():
    glPushAttrib(GL_TRANSFORM_BIT)
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glPopAttrib()

def main():
    CAM_TRANSLATE_STEP = .5
    CAM_ROTATE_STEP = 2.0
    
    pygame.init()
    pygame.key.set_repeat(500,30)
    pygame.display.set_mode((512, 512), OPENGL | DOUBLEBUF)
    pygame.display.set_caption("Maps rendering test")

    options = {'ao': False, 'png': None, 'with_texture': True}
    try:
        options['ao'] = sys.argv[1] == '-ao'
    except:
        pass
        
    try:
        options['png'] = sys.argv[2] if sys.argv[1] == '-png' else None
    except:
        pass
    
    try:
        if os.name == 'morphos':
            # lowlevel module needs to share with pygame display the same TGL base/context
            import _tgl
            lowlevel.setup(_tgl._TinyGLBase, PLATFORM.GL.tglGetContext())
    
        sky = Sky()
        
        camera = Camera()
        player = Player()
        player.camera = camera
        
        if options['ao']:
            map = gen_ao_test_map()
            camera.move(0, 4, 25)
            camera.lookat(0, 0, 0)
            
        elif options['png']:
            map = map_from_png(options['png'])
            camera.move(0, 12, -64)
            camera.dz = -3
            camera.dy = -1
            camera.far = 75

        else:
            map = gen_map()
            camera.pz = -5
            camera.py = 12
            camera.far = 100
            camera.lookat(0, 3, 0)
        
        print "%u node(s) in %u cluster(s)" % (len(map.nodes), len(map))
        print "Computing neightbours..."
        map.compute_neightbours()
        
        if 0:
            for key, cluster in map.iteritems():
                print key, cluster, (cluster.x, cluster.y, cluster.z)
            for node in map.nodes:
                x = node.cube.x
                y = node.cube.y
                z = node.cube.z
                print (x,y,z), hex(id(node))
                for dy in xrange(-1, 2):
                    print
                    for dx in xrange(-1, 2):
                        for dz in xrange(-1, 2):
                            n2 = node[x+dx,y-dy,z+dz]
                            print "0x%08x" % (id(n2) if n2 else 0),
                        print
                    print
        
        print "Processing occlusion..."
        remains = map.process_occlusion()
        print "remains %u visible nodes" % len(remains)
        del remains
                
        gl_init(camera.fov)
        
        clock = pygame.time.Clock()
        
        mouse_trap = False
        
        pygame.mouse.set_visible(not mouse_trap)
        
        a = 0
        
        # Main loop
        glClearColor(0.3, 0.5, 1.0, 1.0)
        while 1:
            # Rendering one time per tick
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            
            camera.render()
            #sky.render()
            
            if options['ao']:
                glRotatef(a, 0, 1, 0)
                #a += 1
            
            if options['with_texture']:
                glEnable(GL_TEXTURE_2D)
            else:
                glDisable(GL_TEXTURE_2D)
            map.render(camera)
            
            glLoadIdentity()
            
            glMatrixMode(GL_PROJECTION)
            glPushMatrix()
            glLoadIdentity()
            glOrtho(-1, 1, -1, 1, 0, 1)
            
            glColor3f(1, 1, 1)
            glBegin(GL_LINES)
            glVertex2f(-0.04, 0)
            glVertex2f(0.04, 0)
            glVertex2f(0, -0.04)
            glVertex2f(0, 0.04)
            glEnd()
            
            glPopMatrix()
            
            pygame.display.flip()
        
            for event in pygame.event.get():                
                if event.type is QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                    return
                    
                if event.type == KEYDOWN:
                    if event.key == K_DOWN:
                        camera.py -= 0.2
                    elif event.key == K_UP:
                        camera.py += 0.2
                    elif event.key == K_m:
                        mouse_trap = not mouse_trap
                    elif event.key == K_t:
                        options['with_texture'] = not options['with_texture']

                elif event.type == MOUSEMOTION:
                    if not options['ao']:
                        dx, dy = event.rel
                        camera.rotate_x(dy)
                        camera.rotate_y(dx)
                        
                        
                        if mouse_trap:
                            pygame.event.set_blocked(MOUSEMOTION)
                            pygame.mouse.set_pos(255, 255)
                            pygame.event.set_allowed(MOUSEMOTION)
                        
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 2:
                        player.forward()
                        
                elif event.type == MOUSEBUTTONUP:
                    if event.button == 2:
                        player.stop()
                        
            player.update()
            clock.tick(30)
            
    finally:
        pygame.display.quit()
        pygame.quit()
      
if __name__ == '__main__':
    OpenGL.CONTEXT_CHECKING = True
    OpenGL.STORE_POINTERS = True
    
    main()
