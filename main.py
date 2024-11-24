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

if __name__ == "__main__":
    import sys
    from optparse import OptionParser

    sys.path.insert(0, "lib")

    parser = OptionParser()
    parser.add_option("-r", "--root", action="store", type="string", dest="root")
    parser.add_option("--width", type="int", dest="width", default=640)
    parser.add_option("--height", type="int", dest="height", default=480)
    parser.add_option("--test", action="store", type="string", dest="test")
    parser.add_option("--nodeid", type="int", dest="nodeid", default=1)
    parser.add_option("--be", "--backend", action="store", dest="ctrl", default="pygame")

    args = parser.parse_args()

    from game import Game
    game = Game(*args)
    game.run()
