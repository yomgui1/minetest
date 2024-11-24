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


from view import RenderMediator
from view.renders import Render

class Map2DTest(Render):
    """This class is designed to see a map as a 2D array.
    It's mainly used during development phase for testing
    of how entities interact with the map.
    """
    
    def __init__(self):
        pass
        
    def render(self):
        pass
    
class Map2DTestMediator(RenderMediator):
    NAME = 'Map2DTest'
    
mediator = Map2DTestMediator(Map2DTest())
