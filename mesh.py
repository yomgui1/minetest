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

import OpenGL.GL as GL
from OpenGL.GL import *

__all__ = ['Face', 'Cuboid', 'Cube']

class Face(object):
    __slots__ = ['vpos', 'texpos']

class Cuboid(object):
    "Parallelepiped textured mesh"

    __slots__ = ['_clid', '_faces', 'rotx', 'roty', 'rotz', 'cx', 'cy', 'cz', 'scale']

    def __init__(self, tw, th, tx0, ty0, cx, cy, cz, sx, sy, sz, scale=1.0):
        self._faces = []
        self._clid = None
        self.rotx = self.roty = self.rotz = 0.0
        self.cx = cx
        self.cy = cy
        self.cz = cz

        ## Generate Cuboid vertices

        # this offset is used to perfectly "join" faces and remove possible holes during rasterizing
        perr = 0.001

        fac = 8 * 2.0 / scale
        x0 = -sx / fac + perr
        x1 =  sx / fac - perr
        y0 = -sy / fac + perr
        y1 =  sy / fac - perr
        z0 = -sz / fac + perr
        z1 =  sz / fac - perr

        p1 = (x0, y0, z0)
        p2 = (x0, y1, z0)
        p3 = (x1, y1, z0)
        p4 = (x1, y0, z0)

        p5 = (x0, y0, z1)
        p6 = (x0, y1, z1)
        p7 = (x1, y1, z1)
        p8 = (x1, y0, z1)

        ## Generate Cuboid faces
        ##
        ## For each 3D corner point (vpos), associate a texture point (texpos)

        # Top
        self.add_face(tw, th, [ p2, p6, p7, p3 ],
                      [ (tx0+sz, ty0+sy), (tx0+sz, ty0+sy+sz), (tx0+sz+sx, ty0+sy+sz), (tx0+sz+sx, ty0+sy) ])

        # Bottom
        self.add_face(tw, th, [ p5, p1, p4, p8 ],
                      [ (tx0+sz+sx, ty0+sy), (tx0+sz+sx, ty0+sy+sz), (tx0+sz+2*sx, ty0+sy+sz), (tx0+sz+2*sx, ty0+sy) ])

        # Left
        self.add_face(tw, th, [ p5, p6, p2, p1 ],
                      [ (tx0, ty0), (tx0, ty0+sy), (tx0+sz, ty0+sy), (tx0+sz, ty0)])

        # Front
        self.add_face(tw, th, [ p1, p2, p3, p4 ],
                      [ (tx0+sz, ty0), (tx0+sz, ty0+sy), (tx0+sz+sx, ty0+sy), (tx0+sz+sx, ty0) ])

        # Right
        self.add_face(tw, th, [ p4, p3, p7, p8 ],
                      [ (tx0+sz+sx, ty0), (tx0+sz+sx, ty0+sy), (tx0+2*sz+sx, ty0+sy), (tx0+2*sz+sx, ty0) ])

        # Rear
        self.add_face(tw, th, [ p8, p7, p6, p5 ],
                      [ (tx0+2*sz+sx, ty0), (tx0+2*sz+sx, ty0+sy), (tx0+2*sz+2*sx, ty0+sy), (tx0+2*sz+2*sx, ty0) ])

    def add_face(self, tw, th, vpos, texpos):
        face = Face()
        face.vpos = vpos
        face.texpos = [ (float(tx) / tw, float(ty) / th) for tx, ty in texpos ]
        self._faces.append(face)

    def render(self):
        # Has rotation?
        if self.rotx or self.roty or self.rotz:
            GL.glPushMatrix()
            GL.glTranslatef(self.cx, self.cy, self.cz)
            if self.rotz:
                GL.glRotatef(self.rotz, 0., 0., 1.)
            if self.roty:
                GL.glRotatef(self.roty, 0., 1., 0.)
            if self.rotx:
                GL.glRotatef(self.rotx, 1., 0., 0.)
            GL.glCallList(self.call_list)
            GL.glPopMatrix()
        else: # Translation only
            GL.glTranslatef(self.cx, self.cy, self.cz)
            GL.glCallList(self.call_list)
            GL.glTranslatef(-self.cx, -self.cy, -self.cz)

    def render_simple(self):
        GL.glTranslatef(self.cx, self.cy, self.cz)
        GL.glCallList(self.call_list)
        GL.glTranslatef(-self.cx, -self.cy, -self.cz)

    def get_call_list(self):
        "Generate the 3D object using faces if not done yet as a GL display list."

        if self._clid is None:
            self._clid = GL.glGenLists(1)

            GL.glNewList(self._clid, GL.GL_COMPILE)

            for face in self._faces:
                GL.glBegin(GL.GL_QUADS)
                GL.glTexCoord2f(*face.texpos[0]); GL.glVertex3f(*face.vpos[0])
                GL.glTexCoord2f(*face.texpos[1]); GL.glVertex3f(*face.vpos[1])
                GL.glTexCoord2f(*face.texpos[2]); GL.glVertex3f(*face.vpos[2])
                GL.glTexCoord2f(*face.texpos[3]); GL.glVertex3f(*face.vpos[3])
                GL.glEnd()

            GL.glEndList()

        return self._clid

    def del_call_list(self):
        self._clid = None

    call_list = property(fget=get_call_list, fdel=del_call_list)

class Cube(object):
    "simple cube textured mesh"

    #__slots__ = ['_clid', '_faces', 'rotx', 'roty', 'rotz', 'cx', 'cy', 'cz', 'scale', '_array', '_count', '_ptr']

    def __init__(self, tw, th, texfaces, cx, cy, cz, ts, scale=1.0):
        self._faces = []
        self._clid = None
        self.rotx = self.roty = self.rotz = 0.0
        self.cx = cx
        self.cy = cy
        self.cz = cz

        ## Generate cube vertices

        # this offset is used to perfectly "join" faces and remove possible holes during rasterizing
        perr = 0.001

        fac = scale / 2.0
        x0 = y0 = z0 = -fac + perr
        x1 = y1 = z1 =  fac - perr

        y0 += 2.0
        y1 += 2.0

        p1 = (x0, y0, z0)
        p2 = (x0, y1, z0)
        p3 = (x1, y1, z0)
        p4 = (x1, y0, z0)

        p5 = (x0, y0, z1)
        p6 = (x0, y1, z1)
        p7 = (x1, y1, z1)
        p8 = (x1, y0, z1)

        ## Generate cube faces
        ##
        ## For each 3D corner point (vpos), associate a texture point (texpos)

        # Top
        tx = texfaces[0][0] * ts
        ty = th - texfaces[0][1] * ts - ts
        self.add_face(tw, th, [ p2, p6, p7, p3 ],
                      [ (tx, ty), (tx, ty+ts), (tx+ts, ty+ts), (tx+ts, ty) ])

        # Bottom
        tx = texfaces[1][0] * ts
        ty = th - texfaces[1][1] * ts - ts
        self.add_face(tw, th, [ p5, p1, p4, p8 ],
                      [ (tx, ty), (tx, ty+ts), (tx+ts, ty+ts), (tx+ts, ty) ])

        # Left
        tx = texfaces[2][0] * ts
        ty = th - texfaces[2][1] * ts - ts
        self.add_face(tw, th, [ p5, p6, p2, p1 ],
                      [ (tx, ty), (tx, ty+ts), (tx+ts, ty+ts), (tx+ts, ty) ])

        # Front
        tx = texfaces[3][0] * ts
        ty = th - texfaces[3][1] * ts - ts
        self.add_face(tw, th, [ p1, p2, p3, p4 ],
                      [ (tx, ty), (tx, ty+ts), (tx+ts, ty+ts), (tx+ts, ty) ])

        # Right
        tx = texfaces[4][0] * ts
        ty = th - texfaces[4][1] * ts - ts
        self.add_face(tw, th, [ p4, p3, p7, p8 ],
                      [ (tx, ty), (tx, ty+ts), (tx+ts, ty+ts), (tx+ts, ty) ])

        # Rear
        tx = texfaces[5][0] * ts
        ty = th - texfaces[5][1] * ts - ts
        self.add_face(tw, th, [ p8, p7, p6, p5 ],
                      [ (tx, ty), (tx, ty+ts), (tx+ts, ty+ts), (tx+ts, ty) ])

    def add_face(self, tw, th, vpos, texpos):
        face = Face()
        face.vpos = vpos
        face.texpos = [ (float(tx) / tw, float(ty) / th) for tx, ty in texpos ]
        self._faces.append(face)

    def render_simple_old(self):
        glTranslatef(self.cx, self.cy, self.cz)
        glCallList(self.call_list)
        glTranslatef(-self.cx, -self.cy, -self.cz)

    def get_call_list(self):
        "Generate the 3D object using faces if not done yet as a GL display list."

        if self._clid is None:
            self._clid = glGenLists(1)

            glNewList(self._clid, GL_COMPILE)

            for face in self._faces:
                glBegin(GL_QUADS)
                glTexCoord2f(*face.texpos[0]); glVertex3f(*face.vpos[0])
                glTexCoord2f(*face.texpos[1]); glVertex3f(*face.vpos[1])
                glTexCoord2f(*face.texpos[2]); glVertex3f(*face.vpos[2])
                glTexCoord2f(*face.texpos[3]); glVertex3f(*face.vpos[3])
                glEnd()

            glEndList()

        return self._clid

    def del_call_list(self):
        self._clid = None

    call_list = property(fget=get_call_list, fdel=del_call_list)
