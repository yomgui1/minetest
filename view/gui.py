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

import gl
from OpenGL import GL

class Widget(object):
    pass
    
class Text(Widget):
    _length = None

    @classmethod
    def get_size(cls, gl, text):
        return gl.get_text_size(text)
        
    @classmethod
    def draw(cls, gl, text, left, top, color=(0, 0, 0, 1)):
        gl.set_color_rgba(*color)
        gl.text(left, top - gl.glyph_height + 1, text)

class Button(Widget):    
    @classmethod
    def draw(cls, gl, text, left, top, width, height, color=(.33, .33, .33, .75)):
        tw, th = Text.get_size(gl, text)
        w = max(width, tw + 2*6)
        h = max(height, th + 2*3)
        
        gl.set_color_rgba(*color)
        gl.draw_rect(left, top-h+1, w, h, 1)
        Text.draw(gl, text, left + (w - tw) / 2, top - 3)
        
        return left, top, w, h
