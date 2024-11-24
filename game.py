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
import controller

class Game(mvc.Facade):
    NAME = "CraftCraft"
    VERSION = "0.0"

    def __init__(self, options, args):
        super(Game, self).__init__()

        Game.options = options
        Game.args = args

        if options.ctrl == 'pygame':
            Game.controller = controller.PyGameController()
        else:
            raise RuntimeError("unknown controller '%s'" % controller)

    @staticmethod
    def run():
        Game.controller.start()
