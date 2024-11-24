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


import os
import mvc

renders = []

def load_renders():
    for root, dirs, files in os.walk(__path__[0]):
        for file in files:
            if file in ['__init__.py']: continue
            
            name, ext = os.path.splitext(file)
            if ext == '.py':
                m = __import__('view.renders.'+name, fromlist=['mediator'])
                renders.append(m)
                
class Render(object):
    @mvc.virtualmethod
    def render(self): pass
