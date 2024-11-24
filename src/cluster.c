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

#include <stdlib.h>
#include <string.h>
#include <assert.h>

#include "cluster.h"

#define LEAF_MIN_RANGE 5

#if 0
#define DLOG dprintf
#else
#define DLOG(x...)
#endif

int depth;

int cluster_bvh_split(Cluster *cluster, BlocksID blocks, BVHNode *root, BVHAxis axis)
{
    BVHNode *left, *right;
    BVHAxis next_axis;
    int min=-1, max=0, range;
    int x, y, z;
    
    if (!root)
    {
        root = bvh_alloc_node(NULL);
        if (!root)
            return -1;
            
        /* Always start by spliting the Y axis */
        axis = BVH_SPLIT_Y;
        
        root->bbox.min_x = root->bbox.min_y = root->bbox.min_z = 0;
        root->bbox.max_x = CLUSTER_SIZE_X;
        root->bbox.max_y = CLUSTER_SIZE_Y;
        root->bbox.max_z = CLUSTER_SIZE_Z;
        
        get_aabb3_sphere_ub(&root->bbox, &root->bsphere);
        
        cluster->bvh_root = root;
        depth = 0;
    }
    else
        depth++;
    
    /* Search where to split the root node.
     * If it's not possible set this root node as a leaf one.
     *
     * Current implementation: <TODO>
     */
    
    /* FIXME: This triple loop is really not efficent! */
    switch (axis)
    {
        case BVH_SPLIT_X:
            for (x=root->bbox.min_x; x < root->bbox.max_x; x++)
            {
                for (z=root->bbox.min_z; z < root->bbox.max_z; z++)
                {
                    for (y=root->bbox.min_y; y < root->bbox.max_y; y++)
                    {
                        int id = blocks[x][z][y];
                        
                        /* not air? */
                        if (id != 0)
                        {
                            if (min == -1)
                                min = x;
                            else if (x > max)
                                max = x;
                        }
                    }
                }
            }
            break;
            
        case BVH_SPLIT_Y:
            for (x=root->bbox.min_x; x < root->bbox.max_x; x++)
            {
                for (z=root->bbox.min_z; z < root->bbox.max_z; z++)
                {
                    for (y=root->bbox.min_y; y < root->bbox.max_y; y++)
                    {
                        int id = blocks[x][z][y];
                        
                        /* not air? */
                        if (id != 0)
                        {
                            if (min == -1)
                                min = y;
                            else if (y > max)
                                max = y;
                        }
                    }
                }
            }
            break;
            
        case BVH_SPLIT_Z:
            for (x=root->bbox.min_x; x < root->bbox.max_x; x++)
            {
                for (z=root->bbox.min_z; z < root->bbox.max_z; z++)
                {
                    for (y=root->bbox.min_y; y < root->bbox.max_y; y++)
                    {
                        int id = blocks[x][z][y];
                        
                        /* not air? */
                        if (id != 0)
                        {
                            if (min == -1)
                                min = z;
                            else if (z > max)
                                max = z;
                        }
                    }
                }
            }
            break;
    }
    
    max++;
    range = max - min;
    
    DLOG("[%u] Node@%p: BBox=[(%u,%u,%u), (%u,%u,%u)], axis=%c, min=%u, max=%u (r=%u)\n", depth, root,
        root->bbox.min_x, root->bbox.min_y, root->bbox.min_z, root->bbox.max_x, root->bbox.max_y, root->bbox.max_z,
        "YZX"[axis], min, max, range);
    
    if (range <= LEAF_MIN_RANGE)
    {
        root->axis = BVH_LEAF;
        depth--;
        DLOG("Node@%p: is a leaf\n", root);
        return 0;
    }
    
    left = bvh_alloc_node(root);
    if (!left)
        return -1;
        
    right = bvh_alloc_node(root);
    if (!right)
    {
        generic_free(left);
        return -1;
    }
    
    root->axis = axis;
    root->left = left;
    root->right = right;
    
    /* Split left and right part using the next split axis */
    next_axis = (axis+1) % 3;
    
    memcpy(&left->bbox, &root->bbox, sizeof(left->bbox));
    memcpy(&right->bbox, &root->bbox, sizeof(right->bbox));
    
    range /= 2;
    
    if (axis == BVH_SPLIT_X)
    {
        right->bbox.min_x = min;
        left->bbox.max_x = max;
        right->bbox.max_x = left->bbox.min_x = range + min;
    }
    else if (axis == BVH_SPLIT_Y)
    {
        right->bbox.min_y = min;
        left->bbox.max_y = max;
        right->bbox.max_y = left->bbox.min_y = range + min;
    }
    else
    {
        right->bbox.min_z = min;
        left->bbox.max_z = max;
        right->bbox.max_z = left->bbox.min_z = range + min;
    }
    
    get_aabb3_sphere_ub(&left->bbox, &left->bsphere);
    get_aabb3_sphere_ub(&right->bbox, &right->bsphere);
    
    DLOG("Node@%p: split left@%p\n", root, left);
    if (!cluster_bvh_split(cluster, blocks, left, next_axis))
    {
        DLOG("Node@%p: split right@%p\n", root, right);
        if (!cluster_bvh_split(cluster, blocks, right, next_axis))
        {
            depth--;
            return 0;
        }
            
        bvh_tree_free(left, NULL);
    }
    else
        generic_free(left);
    
    generic_free(right);
    
    return -1;
}
