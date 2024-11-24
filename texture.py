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

import pygame.image

from OpenGL.GL import *
from OpenGL.GLU import *

class GLTexture:
    """
    Attributes:
        texid: OpenGL texture id
        width: width of the texture in texels unit
        height: height of the texture in texels unit
    """

    texid = None

    def __init__(self, filename, **k):
        self.texid = glGenTextures(1)
        self.load_and_bind(filename, self.texid, **k)

    def load_and_bind(self, filename, texid=0, sky=False, tile=False, mipmap=False):
        "load and bind an opengl texture"

        print "Set texture#%d from file '%s'" % (texid, filename)
        imgsurf = pygame.image.load(filename)
        imgstring = pygame.image.tostring(imgsurf, "RGBA", 1)
        self.width, self.height = imgsurf.get_size()
        glBindTexture(GL_TEXTURE_2D, texid)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_REPEAT)
        if sky:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        elif mipmap:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST_MIPMAP_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        else:
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)

        if mipmap:
            gluBuild2DMipmaps(GL_TEXTURE_2D, GL_RGBA, self.width, self.height, GL_RGBA, GL_UNSIGNED_BYTE, imgstring)
            #for i in xrange(8):
            #    glTexImage2D(GL_TEXTURE_2D, i, GL_RGBA, self.width>>i, self.height>>i, 0,
            #                GL_RGBA, GL_UNSIGNED_BYTE, imgstring)
            #    imgstring = ''.join(imgstring[i:i+4] for i in xrange(0, len(imgstring), 8))

        else:
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, self.width, self.height, 0,
                         GL_RGBA, GL_UNSIGNED_BYTE, imgstring)

    def cleanup(self):
        if self.texid is not None:
            glDeleteTextures(self.texid)
