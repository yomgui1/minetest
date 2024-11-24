/* This file is part of NoCurve.
*
*    NoCurve is free software: you can redistribute it and/or modify
*    it under the terms of the GNU General Public License as published by
*    the Free Software Foundation, either version 3 of the License, or
*    (at your option) any later version.
*
*    NoCurve is distributed in the hope that it will be useful,
*    but WITHOUT ANY WARRANTY; without even the implied warranty of
*    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
*    GNU General Public License for more details.
*
*    You should have received a copy of the GNU General Public License
*    along with NoCurve.  If not, see <http://www.gnu.org/licenses/>.
*/

#ifndef SCENE_H
#define SCENE_H

#include <stdint.h>

/* Various world dimenssions */
/* keep them a power of 2 for optimizations */
#define CLUSTER_SIZE_X 16
#define CLUSTER_SIZE_Z 16
#define CLUSTER_SIZE_Y 128
#define WORLD_CLUSTER_X_SHIFT 4
#define WORLD_CLUSTER_Z_SHIFT 4

#define WORLD_CLUSTER_X (1 << WORLD_CLUSTER_X_SHIFT)
#define WORLD_CLUSTER_Z (1 << WORLD_CLUSTER_Z_SHIFT)
#define WORLD_CLUSTER_X_MASK (WORLD_CLUSTER_X - 1)
#define WORLD_CLUSTER_Z_MASK (WORLD_CLUSTER_Z - 1)
#define CLUSTER_SIZE_X_MASK (CLUSTER_SIZE_X - 1)
#define CLUSTER_SIZE_Z_MASK (CLUSTER_SIZE_Z - 1)
#define CLUSTER_SIZE_Y_MASK (CLUSTER_SIZE_Y - 1)

#define BLOCK_COUNT_X (WORLD_CLUSTER_X*CLUSTER_SIZE_X)
#define BLOCK_COUNT_Z (WORLD_CLUSTER_Z*CLUSTER_SIZE_Z)
#define BLOCK_COUNT_Y CLUSTER_SIZE_Y

/* Blocks array access macros */
#define OFFSET_FROM_POSITION(x, y, z) ((x)*CLUSTER_SIZE_Y*CLUSTER_SIZE_Z+(z)*CLUSTER_SIZE_Y+(y))
#define POSITION_FROM_OFFSET(n, xv, yv, zv) ({ typeof(n) _n = (n); (yv) = _n & CLUSTER_SIZE_Y_MASK; })

#define BLOCKS_PER_CLUSTER (CLUSTER_SIZE_X*CLUSTER_SIZE_Z*CLUSTER_SIZE_Y)

typedef struct BlockInfo {
	uint16_t id:8;
	uint16_t occlusion:6;
} BlockInfo;

typedef uint8_t BlocksID[CLUSTER_SIZE_X][CLUSTER_SIZE_Z][CLUSTER_SIZE_Y];
typedef uint8_t HeightMap[CLUSTER_SIZE_Z][CLUSTER_SIZE_X];

extern void *generic_malloc(size_t);
extern void generic_free(void *);

#endif
