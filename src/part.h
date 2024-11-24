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

#ifndef PART_H
#define PART_H

#include "geometry.h"

#include <stdint.h>

struct BVHNode;
typedef struct BVHNode BVHNode;

typedef enum {
    BVH_SPLIT_Y=0,
    BVH_SPLIT_Z,
    BVH_SPLIT_X,
    BVH_LEAF,
} BVHAxis;

struct BVHNode {
    struct {
        uint32_t axis:2;                /* split plane axis (BVH_LEAF indicates a leaf node) */
    };
    
    BVHNode *parent;                    /* parent node, NULL if root */
    BVHNode *left, *right;              /* left and right child (if node not a leaf) */
    BSphere bsphere;                    /* node bounding sphere (center, diameter) */
    AABB3ub bbox;                       /* node bbox */
    void *udata;
};

/* alloc BVHNode on heap */
extern BVHNode *bvh_alloc_node(BVHNode *parent);

/* free all nodes in a BVH tree */
extern void bvh_tree_free(BVHNode *root, void (*user_free)(void *));

/* return BVH node containing the given point (point given in cluster origin).
 * This function always succeed if x,y,z are in range.
 */
extern BVHNode *bvh_query(BVHNode *root, float x, float y, float z);

#endif
