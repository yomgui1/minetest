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

import ctypes

import OpenGL.GL as GL
from OpenGL import constants

import lowlevel
from texture import GLTexture
from mesh import *

## BlocksID data obtained from minecraft blender add-ons.
## tinted data added by me
##
#Blockdata is: [name, diffusecolour RGB triple, (textureID_top, textureID_bottom, textureID_sides) triple or None if nonsquare, custommodel etc]
# Texture IDs are the 1d (2d) count of location of their 16x16 square within terrain.png in minecraft.jar
# Order for Blender cube face creation is: [bottom, top, right, front, left, back]

BLOCKDATA = {
    0: ['Air'],
    1: ['Stone', (116,116,116), [1]*6],
    2: ['GrassBlock', (95,159,53), [2,0,3,3,3,3], [0, 1, 0, 0, 0, 0]], # top tinted
    3: ['Dirt', (150, 108, 74), [2]*6],
    4: ['Cobblestone', (94,94,94), [16]*6],
    5: ['WoodenPlank', (159,132,77), [4]*6],
    6: ['Sapling', (0,100,0), [15]*6, 'plane'],
    7: ['Bedrock', [51,51,51], [17]*6],
    8: ['Water', (31,85,255), [223]*6],
    9: ['WaterStat', (62,190,255), [223]*6],
    10: ['Lava', (252,0,0), [255]*6],
    11: ['LavaStat', (230,0,0), [255]*6],
    12: ['Sand', (214,208,152), [18]*6],
    13: ['Gravel', (154,135,135), [19]*6],
    14: ['GoldOre', (252,238,75), [32]*6],
    15: ['IronOre', (216,175,147), [33]*6],
    16: ['CoalOre', (69,69,69), [34]*6],
    17: ['Wood', (76,61,38), [21,21,20,20,20,20]],
    18: ['Leaves', (99,128,15,0), [52]*6, [1]*6], # tinted
    19: ['Sponge', (206,206,70), [48]*6],
    20: ['Glass', (254,254,254,0), [49]*6],
    21: ['LapisLazuliOre', (28,87,198), [160]*6],
    22: ['LapisLazuliBlock', (25,90,205), [144]*6],
    23: ['Dispenser', (42,42,42), [62,62,45,46,45,45]],
    24: ['Sandstone', (215,209,153), [208,176,192,192,192,192]],
    25: ['NoteBlock', (145,88,64), [74]*6],
    26: ['Bed'],
    27: ['PwrRail', (204,93,22), [163]*6, 'xplane'],
    28: ['DetRail', (134,101,100), [195]*6, 'xplane'],
    29: ['StickyPiston', (114,120,70), [109,106,108,108,108,108], 'XD', 'pstn'],
    30: ['Cobweb', (237,237,237), [11]*6, 'plane'],
    31: ['TallGrass', (52,79,45), [39]*6, [1]*6, 'plane'],
    32: ['DeadBush', (148,100,40), [55]*6, 'plane'],
    33: ['Piston', (114,120,70), [109,107,108,108,108,108], 'XD', 'pstn'],
    34: ['PistonHead', (188,152,98), [180,107,180,180,180,180]],	#or top is 106 if sticky (extra data)
    35: ['Wool', (235,235,235), [64]*6, 'XD'],
    37: ['Dandelion', (204,211,2), [13]*6, 'cross'],
    38: ['Rose', (247,7,15), [12]*6, 'cross'],
    39: ['BrownMushrm', (204,153,120), [29]*6, 'cross'],
    40: ['RedMushrm', (226,18,18), [28]*6, 'cross'],
    41: ['GoldBlock', (255,241,68), [23]*6],
    42: ['IronBlock'],
    43: ['DoubleSlabs', (255,255,0), [6,6,5,5,5,5]],
    44: ['Slabs', (255,255,0), [6,6,5,5,5,5], 'slab'],
    45: ['BrickBlock', (124,69,24), [7]*6],
    46: ['TNT', (219,68,26), [10,9,8,8,8,8]],
    47: ['Bookshelf', (180,144,90), [35,4,4,4,4,4]],
    48: ['MossStone', (61,138,61), [36]*6],
    49: ['Obsidian', (60,48,86), [37]*6],
    50: ['Torch', (240,150,50,0), [80]*6, 'torch'],
    51: ['Fire'],
    52: ['MonsterSpawner', (27,84,124,0), [65]*6],
    53: ['WoodenStairs', (159,132,77), [4]*10, 'stairs'],
    54: ['Chest', (164,114,39), [25,25,26,27,26,26], 'XD', 'chest'],    #texface ordering is wrong
    55: ['RedStnWire', (255,0,3), [165]*6, [1]*6, 'sticky'], # special occlusion
    56: ['DiamondOre', (93,236,245), [50]*6],
    57: ['DiamondBlock', (93,236,245), [24]*6],
    58: ['CraftingTbl', (160,105,60), [43,43,59,60,59,60]],
    59: ['Seeds', (160,184,0,0), [180,180,94,94,94,94]],
    60: ['Farmland', (69,41,21), [2,87,2,2,2,2]],
    61: ['Furnace', (42,42,42), [62,62,45,44,45,45]],		#[bottom, top, right, front, left, back]
    62: ['Burnace', (50,42,42), [62,62,45,61,45,45]],
    63: ['SignPost'],
    64: ['WoodDoor', (145,109,56), [97,97,81,81,81,81], 'pane'],
    65: ['Ladder', (142,115,60), [83], 'sticky'],
    66: ['Rail', (172,136,82), [128,180,180,180,180,180], 'xplane'],
    67: ['CobbleStairs', (77,77,77), [16]*10, 'stairs'],
    68: ['WallSign'],
    69: ['Lever', (105,84,51), [96]*6+[1]*6, 'lever'],
    70: ['StnPressPlate', (110,110,110), [1]*6, 'level'],
    71: ['IronDoor', (183,183,183), [98,98,82,82,82,82], 'pane'],
    72: ['WdnPressPlate', (159,132,77), [4]*6, 'level'],
    73: ['RedstoneOre', (151,3,3), [51]*6],
    74: ['RedstoneOreGlowing', (255,3,3), [51]*6],
    75: ['RedstoneTorchOff', (86,0,0), [115]*6, 'torch'],
    76: ['RedstoneTorchOn', (253,0,0), [99]*6, 'torch'],
    77: ['StoneButton', (116,116,116), [1]*6, 'btn'],
    78: ['Snow', (240,240,240), [66]*6, 'level'],
    79: ['Ice', (220,220,255), [67]*6],
    80: ['SnowBlock', (240,240,240), [66]*6],
    81: ['Cactus', (20,141,36), [71,69,70,70,70,70], 'cube2'],
    82: ['ClayBlock', (170,174,190), [72]*6],
    83: ['SugarCane', (130,168,89,0), [73]*6],
    84: ['Jukebox', (145,88,64), [75,74,74,74,74,74]],
    85: ['Fence', (160,130,70), [4]*6],
    86: ['Pumpkin', (227,144,29), [118,102,118,118,118,118]],
    87: ['Netherrack', (137,15,15), [103]*6],
    88: ['SoulSand', (133,109,94), [104]*6],
    89: ['Glowstone', (114,111,73), [105]*6],
    90: ['Portal', (150,90,180), None],
    91: ['JackOLantern',(227,144,29), [118,102,118,119,118,118]],
    92: ['Cake', (184,93,39,0), [124,121,122,122,122,122], 'XD', 'cake'],
    93: ['RedRepOff', (176,176,176), [131]*6, 'xdcircuit', 'redrep'],
    94: ['RedRepOn', (176,176,176), [147]*6, 'xdcircuit', 'redrep'],
    95: ['InvibleBedrock'],
    96: ['Trapdoor', (117,70,34), [84]*6, 'xplane'],
    97: ['HiddenSfish', (116,116,116), [1]*6],
    98: ['StoneBricks', (100,100,100), [54]*6],
    99: ['HugeBrownMrm'],
    100: ['HugeRedMrm'],
    101: ['IronBars', (171,171,173), [85]*6, 'pane'],
    102: ['GlassPane', (254,254,254), [49]*6, 'pane'],
    103: ['Melon', (166,166,39), [137,137,136,136,136,136]],
    104: ['PumpkinStem'],
    105: ['MelonStem'],
    106: ['Vines', (39,98,13), [143]*6, 'XD', 'wallface'],
    107: ['FenceGate', (143,115,73)],
    108: ['BrickStairs', (135,74,58), [7]*10, 'stairs'],
    109: ['StoneBrickStairs', (100,100,100), [54]*10, 'stairs'],
    110: ['Mycelium', (122,103,108), [2,78,77,77,77,77]],
    111: ['LilyPad', (12,94,19), [76]*6, 'level'],
    112: ['NethrBrick', (48,24,28), [224]*6],
    113: ['NethrBrickFence', (48,24,28), [224]*6, 'XD', 'fence'],
    114: ['NethrBrickStairs', (48,24,28), [224]*10, 'stairs'],
    115: ['NethrWart'],
    116: ['EnchantTab', (116,30,29), [167,166,182,182,182,182], 'none', '12high-enchantable'],
    117: ['BrewStnd'],
    118: ['Cauldron'],
    119: ['EndPortal', (0,0,0), None],
    120: ['EndPortalFrame', (144,151,110), [175,158,159,159,159,159]],
    121: ['EndStone', (144,151,110), [175]*6],
    122: ['DragonEgg', (0,0,0)]
}

MESHES = {}

NON_SOLID_BLOCKS = (6,8,9,10,11,20,26,27,28,30,31,32,34,36,37,38,39,40,44,
                    50,52,52,53,55,59,63,64,65,66,67,68,69,70,71,72,75,76,77,
                    78,83,85,90,92,93,94,96,99,100,101,102,104,105,106,107,108,
                    109,111,113,114,115,117,118,119,122,126,127,128,131,132,
                    134,135,136,138,139,140,141,142,143,145,147,148,149,150,
                    151,154,156,157,160,163,164,166,167,168,169,171,175)

def is_block_solid(idx): return idx not in NON_SOLID_BLOCKS

def gen_texture_array(mesh_type, tw, th, texfaces, ts):
    "Generate all texture coordinates for a cube as a float list"

    t = []

    if mesh_type == lowlevel.MESH_STICKY:
        tx = texfaces[0][0] * ts
        ty = th - texfaces[0][1] * ts - ts
        t += [ (tx, ty), (tx+ts, ty), (tx+ts, ty+ts), (tx, ty+ts) ]

    elif mesh_type in (lowlevel.MESH_TORCH, lowlevel.MESH_LEVER):
        # bottom
        tx = texfaces[0][0] * ts
        ty = th - texfaces[0][1] * ts - ts
        t += [ (tx+7, ty+8), (tx+9, ty+8), (tx+9, ty+10), (tx+7, ty+10) ]

        # Top
        tx = texfaces[1][0] * ts
        ty = th - texfaces[1][1] * ts - ts
        t += [ (tx+7, ty+8), (tx+9, ty+8), (tx+9, ty+10), (tx+7, ty+10) ]

        # Right
        tx = texfaces[2][0] * ts
        ty = th - texfaces[2][1] * ts - ts
        t += [ (tx+7, ty), (tx+9, ty), (tx+9, ty+8), (tx+7, ty+8) ]

        # Left
        tx = texfaces[3][0] * ts
        ty = th - texfaces[3][1] * ts - ts
        t += [ (tx+7, ty), (tx+9, ty), (tx+9, ty+8), (tx+7, ty+8) ]

        # Front
        tx = texfaces[4][0] * ts
        ty = th - texfaces[4][1] * ts - ts
        t += [ (tx+7, ty), (tx+9, ty), (tx+9, ty+8), (tx+7, ty+8) ]

        # Rear
        tx = texfaces[5][0] * ts
        ty = th - texfaces[5][1] * ts - ts
        t += [ (tx+7, ty), (tx+9, ty), (tx+9, ty+8), (tx+7, ty+8) ]

        if mesh_type == lowlevel.MESH_LEVER:
            # bottom
            tx = texfaces[6][0] * ts
            ty = th - texfaces[6][1] * ts - ts
            t += [ (tx+5, ty+2), (tx+11, ty+2), (tx+11, ty+5), (tx+5, ty+5) ]

            # Top
            tx = texfaces[7][0] * ts
            ty = th - texfaces[7][1] * ts - ts
            t += [ (tx+5, ty+13), (tx+11, ty+13), (tx+11, ty+16), (tx+5, ty+16) ]

            # Right
            tx = texfaces[8][0] * ts
            ty = th - texfaces[8][1] * ts - ts
            t += [ (tx+2, ty+5), (tx+5, ty+5), (tx+5, ty+13), (tx+2, ty+13) ]

            # Left
            tx = texfaces[9][0] * ts
            ty = th - texfaces[9][1] * ts - ts
            t += [ (tx+11, ty+5), (tx+14, ty+5), (tx+14, ty+13), (tx+14, ty+13) ]

            # Front
            tx = texfaces[10][0] * ts
            ty = th - texfaces[10][1] * ts - ts
            t += [ (tx+5, ty+5), (tx+11, ty+5), (tx+11, ty+13), (tx+5, ty+13) ]

    else: # CUBE
        # Bottom
        tx = texfaces[0][0] * ts
        ty = th - texfaces[0][1] * ts - ts
        t += [ (tx, ty), (tx+ts, ty), (tx+ts, ty+ts), (tx, ty+ts) ]

        if mesh_type == lowlevel.MESH_STAIRS:
            # Top low
            tx = texfaces[1][0] * ts
            ty = th - texfaces[1][1] * ts - ts
            t += [ (tx, ty), (tx+ts, ty), (tx+ts, ty+ts-8), (tx, ty+ts-8) ]

            # Right
            tx = texfaces[2][0] * ts
            ty = th - texfaces[2][1] * ts - ts
            t += [ (tx, ty), (tx+ts, ty), (tx+ts, ty+ts), (tx, ty+ts) ]

            # Left low
            tx = texfaces[3][0] * ts
            ty = th - texfaces[3][1] * ts - ts
            t += [ (tx, ty), (tx, ty+ts-8), (tx+ts, ty+ts-8), (tx+ts, ty) ]

            # Front low
            tx = texfaces[4][0] * ts
            ty = th - texfaces[4][1] * ts - ts
            t += [ (tx, ty), (tx+ts, ty), (tx+ts, ty+ts-8), (tx, ty+ts-8) ]

            # Rear low
            tx = texfaces[5][0] * ts
            ty = th - texfaces[5][1] * ts - ts
            t += [ (tx, ty), (tx+ts, ty), (tx+ts, ty+ts-8), (tx, ty+ts-8) ]

            # Top hi
            tx = texfaces[6][0] * ts
            ty = th - texfaces[6][1] * ts - ts
            t += [ (tx, ty+8), (tx+ts, ty+8), (tx+ts, ty+ts), (tx, ty+ts) ]

            # Left hi
            tx = texfaces[7][0] * ts
            ty = th - texfaces[7][1] * ts - ts
            t += [ (tx, ty+8), (tx+ts, ty+8), (tx+ts, ty+ts), (tx, ty+ts) ]

            # Front hi
            tx = texfaces[8][0] * ts
            ty = th - texfaces[8][1] * ts - ts
            t += [ (tx+8, ty+8), (tx+ts, ty+8), (tx+ts, ty+ts), (tx+8, ty+ts) ]

            # Rear hi
            tx = texfaces[9][0] * ts
            ty = th - texfaces[9][1] * ts - ts
            t += [ (tx+8, ty+8), (tx+ts, ty+8), (tx+ts, ty+ts), (tx+8, ty+ts) ]

        else:
            # Top
            tx = texfaces[1][0] * ts
            ty = th - texfaces[1][1] * ts - ts
            t += [ (tx, ty), (tx+ts, ty), (tx+ts, ty+ts), (tx, ty+ts) ]

            # Right
            tx = texfaces[2][0] * ts
            ty = th - texfaces[2][1] * ts - ts
            t += [ (tx, ty), (tx+ts, ty), (tx+ts, ty+ts), (tx, ty+ts) ]

            # Front
            tx = texfaces[3][0] * ts
            ty = th - texfaces[3][1] * ts - ts
            t += [ (tx, ty), (tx+ts, ty), (tx+ts, ty+ts), (tx, ty+ts) ]

            # Left
            tx = texfaces[4][0] * ts
            ty = th - texfaces[4][1] * ts - ts
            t += [ (tx, ty), (tx+ts, ty), (tx+ts, ty+ts), (tx, ty+ts) ]

            # Rear
            tx = texfaces[5][0] * ts
            ty = th - texfaces[5][1] * ts - ts
            t += [ (tx, ty), (tx+ts, ty), (tx+ts, ty+ts), (tx, ty+ts) ]

    a = []
    for tx, ty in t:
        a.append(float(tx) / tw)
        a.append(float(ty) / th)

    return a

class Entity(object):
    def __init__(self, texname, hasalpha=False):
        self._Cuboids = []
        self._texture = GLTexture(texname)
        self.hasalpha = hasalpha
        self.create_mesh(self._texture.width, self._texture.height)

    def set_position(self, x, y, z):
        for cube in self._Cuboids:
            cube.cx = x
            cube.cy = y
            cube.cz = z

    def render(self):
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texture.texid)

        if self.hasalpha:
            GL.glDisable(GL.GL_CULL_FACE)
        else:
            GL.glDisable(GL.GL_ALPHA_TEST)

        self._render()

        GL.glEnable(GL.GL_CULL_FACE)
        if self.hasalpha:
            GL.glEnable(GL.GL_ALPHA_TEST)

    def _render(self):
        GL.glDisable(GL.GL_CULL_FACE)
        if self.hasalpha:
            GL.glEnable(GL.GL_ALPHA_TEST)

        self._Cuboids[0].render()
        self._Cuboids[1].render()
        self._Cuboids[2].render()
        self._Cuboids[3].render()
        if len(self._Cuboids) > 4:
            self._Cuboids[4].render()
            self._Cuboids[5].render()

class Mesh(lowlevel.Mesh):
    __slots__ = ['_texture']

    _texture = None

    def __new__(cls, mesh_type, texfaces,
                alpha=0, translucent=0, tinted=None, level=0):
        # I don't want put this texture load in the class definition
        # as the module may be called before the display initialisation.
        # Or the OpenGL context is the wrong one!

        if Mesh._texture is None:
            Mesh._texture = GLTexture('data/terrain.png', mipmap=1)

        a = gen_texture_array(mesh_type, Mesh._texture.width, Mesh._texture.height, texfaces, 16)
        texels = (constants.GLfloat * len(a))(*a)

        if tinted:
            tinted = (constants.GLfloat * len(tinted))(*tinted)
            mesh = super(Mesh, cls).__new__(cls, mesh_type, Mesh._texture.texid, texels, tinted)
        else:
            mesh = super(Mesh, cls).__new__(cls, mesh_type, Mesh._texture.texid, texels)

        mesh.translucent = translucent
        mesh.alpha = alpha or translucent
        mesh.ao = not (translucent or alpha)
        mesh.level = level
        return mesh

class MeshCube(Mesh):
    __slots__ = []

    def __new__(cls, texfaces, *args, **kwds):
        return super(MeshCube, cls).__new__(cls, lowlevel.MESH_CUBE, texfaces, *args, **kwds)

class MeshCube2(Mesh):
    __slots__ = []

    def __new__(cls, texfaces, *args, **kwds):
        kwds['alpha'] = 1
        mesh = super(MeshCube2, cls).__new__(cls, lowlevel.MESH_CUBE2, texfaces, *args, **kwds)
        mesh.ao = 1
        return mesh

class MeshPlane(Mesh):
    __slots__ = []

    def __new__(cls, texfaces, *args, **kwds):
        kwds['alpha'] = 1
        return super(MeshPlane, cls).__new__(cls, lowlevel.MESH_PLANE, texfaces, *args, **kwds)

class MeshSlab(Mesh):
    __slots__ = []

    def __new__(cls, texfaces, *args, **kwds):
        kwds['alpha'] = 1
        return super(MeshSlab, cls).__new__(cls, lowlevel.MESH_SLAB, texfaces, *args, **kwds)

class MeshXPlane(Mesh):
    __slots__ = []

    def __new__(cls, texfaces, *args, **kwds):
        kwds['alpha'] = 1
        kwds['level'] = 1
        return super(MeshXPlane, cls).__new__(cls, lowlevel.MESH_XPLANE, texfaces, *args, **kwds)

class MeshLevel(Mesh):
    __slots__ = []

    def __new__(cls, texfaces, *args, **kwds):
        kwds['alpha'] = 1
        kwds['level'] = 1
        return super(MeshLevel, cls).__new__(cls, lowlevel.MESH_CUBE, texfaces, *args, **kwds)

class MeshSticky(Mesh):
    __slots__ = []

    def __new__(cls, texfaces, *args, **kwds):
        kwds['alpha'] = 1
        return super(MeshSticky, cls).__new__(cls, lowlevel.MESH_STICKY, texfaces, *args, **kwds)

class MeshStairs(Mesh):
    __slots__ = []

    def __new__(cls, texfaces, *args, **kwds):
        kwds['alpha'] = 1
        return super(MeshStairs, cls).__new__(cls, lowlevel.MESH_STAIRS, texfaces, *args, **kwds)

class MeshPane(Mesh):
    __slots__ = []

    def __new__(cls, texfaces, *args, **kwds):
        kwds['alpha'] = 1
        return super(MeshPane, cls).__new__(cls, lowlevel.MESH_PANE, texfaces, *args, **kwds)

class MeshCross(Mesh):
    __slots__ = []

    def __new__(cls, texfaces, *args, **kwds):
        kwds['alpha'] = 1
        return super(MeshCross, cls).__new__(cls, lowlevel.MESH_CROSS, texfaces, *args, **kwds)

class MeshTorch(Mesh):
    __slots__ = []

    def __new__(cls, texfaces, *args, **kwds):
        kwds['alpha'] = 1
        return super(MeshTorch, cls).__new__(cls, lowlevel.MESH_TORCH, texfaces, *args, **kwds)

class MeshLever(Mesh):
    __slots__ = []

    def __new__(cls, texfaces, *args, **kwds):
        kwds['alpha'] = 1
        return super(MeshLever, cls).__new__(cls, lowlevel.MESH_LEVER, texfaces, *args, **kwds)

class Humanoid(Entity):
    def __init__(self, *a, **k):
        super(Humanoid, self).__init__(*a, **k)

    def create_mesh(self, tw, th):
        self._Cuboids.append(Cuboid(tw, th,  0,  0,  0.25, 0.75, 0.0, 4, 12, 4)) # Left leg
        self._Cuboids.append(Cuboid(tw, th,  0,  0, -0.25, 0.75, 0.0, 4, 12, 4)) # Right leg
        self._Cuboids.append(Cuboid(tw, th, 16,  0,  0.00, 2.25, 0.0, 8, 12, 4)) # Body
        self._Cuboids.append(Cuboid(tw, th, 40,  0,  0.75, 2.25, 0.0, 4, 12, 4)) # Left arm
        self._Cuboids.append(Cuboid(tw, th, 40,  0, -0.75, 2.25, 0.0, 4, 12, 4)) # Right arm
        self._Cuboids.append(Cuboid(tw, th,  0, 16,  0.00, 3.50, 0.0, 8,  8, 8)) # Head

class Zombie(Humanoid):
    pass

class Skeleton(Zombie):
    def __init__(self, *a, **k):
        super(Skeleton, self).__init__(*a, **k)

    def create_mesh(self, tw, th):
        self._Cuboids.append(Cuboid(tw, th,  0,  2,  0.25, 0.75, 0.0, 2, 12, 2)) # Left leg
        self._Cuboids.append(Cuboid(tw, th,  0,  2, -0.25, 0.75, 0.0, 2, 12, 2)) # Right leg
        self._Cuboids.append(Cuboid(tw, th, 16,  0,  0.00, 2.25, 0.0, 8, 12, 4)) # Body
        self._Cuboids.append(Cuboid(tw, th, 40,  2,  0.65, 2.25, 0.0, 2, 12, 2)) # Left arm
        self._Cuboids.append(Cuboid(tw, th, 40,  2, -0.65, 2.25, 0.0, 2, 12, 2)) # Right arm
        self._Cuboids.append(Cuboid(tw, th,  0, 16,  0.00, 3.50, 0.0, 8,  8, 8)) # Head

class Creeper(Humanoid):
    def __init__(self, *a, **k):
        super(Creeper, self).__init__(*a, **k)

    def create_mesh(self, tw, th):
        self._Cuboids.append(Cuboid(tw, th,  0,  6,  0.25, 0.75, 0.0, 4,  6, 4)) # Left leg
        self._Cuboids.append(Cuboid(tw, th,  0,  6, -0.25, 0.75, 0.0, 4,  6, 4)) # Right leg
        self._Cuboids.append(Cuboid(tw, th, 16,  0,  0.00, 2.25, 0.0, 8, 12, 4)) # Body
        self._Cuboids.append(Cuboid(tw, th,  0, 16,  0.00, 3.50, 0.0, 8,  8, 8)) # Head

class Quadruped(Entity):
    def __init__(self, *a, **k):
        super(Quadruped, self).__init__(*a, **k)

    def create_mesh(self, tw, th):
        self._Cuboids.append(Cuboid(tw, th,  0,  0,  0.40, 0.50,  1.00, 4, 12, 4)) # Front Left leg
        self._Cuboids.append(Cuboid(tw, th,  0,  0, -0.40, 0.50,  1.00, 4, 12, 4)) # Front Right leg
        self._Cuboids.append(Cuboid(tw, th,  0,  0,  0.40, 0.50, -1.00, 4, 12, 4)) # Rear Left leg
        self._Cuboids.append(Cuboid(tw, th,  0,  0, -0.40, 0.50, -1.00, 4, 12, 4)) # Rear Right leg
        self._Cuboids.append(Cuboid(tw, th, 28,  2,  0.00, 1.75,  0.00, 8, 16, 6, 1.4)) # Body
        self._Cuboids.append(Cuboid(tw, th,  0, 18,  0.00, 2.00, -2.00, 6,  6, 8, 1.4)) # Head

        self._Cuboids[4].rotx = -90

class SheepFur(Quadruped):
    def __init__(self, *a, **k):
        super(SheepFur, self).__init__(*a, **k)

    def create_mesh(self, tw, th):
        self._Cuboids.append(Cuboid(tw, th,  0,  0,  0.40, 0.50,  1.00, 4, 12, 4)) # Front Left leg
        self._Cuboids.append(Cuboid(tw, th,  0,  0, -0.40, 0.50,  1.00, 4, 12, 4)) # Front Right leg
        self._Cuboids.append(Cuboid(tw, th,  0,  0,  0.40, 0.50, -1.00, 4, 12, 4)) # Rear Left leg
        self._Cuboids.append(Cuboid(tw, th,  0,  0, -0.40, 0.50, -1.00, 4, 12, 4)) # Rear Right leg
        self._Cuboids.append(Cuboid(tw, th, 28,  2,  0.00, 1.75,  0.00, 8, 16, 6, 1.4)) # Body
        self._Cuboids.append(Cuboid(tw, th,  0, 20,  0.00, 2.00, -2.00, 6,  6, 6, 1.4)) # Head

        self._Cuboids[4].rotx = -90

class Pig(Quadruped):
    def __init__(self, *a, **k):
        super(Pig, self).__init__(*a, **k)

    def create_mesh(self, tw, th):
        self._Cuboids.append(Cuboid(tw, th,  0,  6,  0.40, 0.50,  1.00,  4,  6, 4)) # Front Left leg
        self._Cuboids.append(Cuboid(tw, th,  0,  6, -0.40, 0.50,  1.00,  4,  6, 4)) # Front Right leg
        self._Cuboids.append(Cuboid(tw, th,  0,  6,  0.40, 0.50, -1.00,  4,  6, 4)) # Rear Left leg
        self._Cuboids.append(Cuboid(tw, th,  0,  6, -0.40, 0.50, -1.00,  4,  6, 4)) # Rear Right leg
        self._Cuboids.append(Cuboid(tw, th, 28,  0,  0.00, 1.50,  0.00, 10, 16, 8)) # Body
        self._Cuboids.append(Cuboid(tw, th,  0, 16,  0.00, 1.25, -2.00,  8,  8, 8)) # Head

        self._Cuboids[4].rotx = -90


def EntityFactory(type):
    if type == 'human':
        return Humanoid('data/char.png')
    if type == 'zombie':
        return Zombie('data/zombie.png')
    if type == 'skeleton':
        return Skeleton('data/skeleton.png', hasalpha=True)
    if type == 'creeper':
        return Creeper('data/creeper.png')
    if type == 'sheep':
        return Quadruped('data/sheep.png')
    if type == 'sheep_fur':
        return SheepFur('data/sheep_fur.png')
    if type == 'pig':
        return Pig('data/pig.png')

MESH_TYPES = { 'cube2': MeshCube2,
               'plane': MeshPlane,
               'xplane': MeshXPlane,
               'cross': MeshCross,
               'torch': MeshTorch,
               'slab': MeshSlab,
               'level': MeshLevel,
               'stairs': MeshStairs,
               'pane': MeshPane,
               'sticky': MeshSticky,
               'lever': MeshLever,
             }

def MeshFactory(idx):
    mesh = MESHES.get(idx)
    if mesh:
        return mesh

    data = BLOCKDATA.get(idx)
    if not data:
        return

    cls = MeshCube
    tinted = None

    if len(data) > 3:
        color, texdata, extra = data[1:4]
        if isinstance(extra, list):
            tinted = extra
            if len(data) > 4:
                cls = MESH_TYPES.get(data[4], MeshCube)
        else:
            cls = MESH_TYPES.get(extra, MeshCube)

    elif len(data) > 2:
        color, texdata = data[1:3]
    else:
        return

    if not texdata:
        return

    if tinted:
        color_tinted = [ v/255. for v in color[:3] ]
        color_plain = [1]*3
        tinted_colors = []
        for v in tinted:
            if v:
                tinted_colors += color_tinted
            else:
                tinted_colors += color_plain
    else:
        tinted_colors = None

    mesh = cls([ (n%16, n/16) for n in texdata ],
               tinted=tinted_colors,
               alpha=len(color)==4,
               translucent=(idx in (8, 9, 10, 11, 95)))
    if mesh.type == lowlevel.MESH_CUBE:
        mesh.occlusion = 63
    MESHES[idx] = mesh

    return mesh
