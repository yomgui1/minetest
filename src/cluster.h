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

#ifndef CLUSTER_H
#define CLUSTER_H

#include "scene.h"
#include "part.h"
#include "geometry.h"

typedef struct {
	BlocksID	blocks;			/* array of block's IDs */
	HeightMap	heightmap;		/* heightmap (ZX order) giving heighest block touch by skylight */
	AABB3i		bbox;			/* Bounding box */
	int			x, z;			/* Position in world coordinates */
} Cluster;

/* Recursively split the cluster blocks and set the cluster->bvh_root pointer
 * Must be called with root=NULL and x=y=z=0 to start.
 */
extern int cluster_bvh_split(Cluster *cluster, BlocksID blocks, BVHNode *root, BVHAxis axis);

#endif
