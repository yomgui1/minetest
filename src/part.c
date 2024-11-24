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

#include "part.h"
#include "scene.h"

#include "stdlib.h" /* for NULL */

BVHNode *bvh_alloc_node(BVHNode *parent)
{
    BVHNode *node = generic_malloc(sizeof(BVHNode));
    
    if (node)
        node->parent = parent;
    node->left = node->right = NULL;
    node->udata = NULL;
    
    return node;
}

void bvh_tree_free(BVHNode *root, void (*user_free)(void *))
{
    if (root->axis != BVH_LEAF)
    {
        bvh_tree_free(root->left, user_free);
        bvh_tree_free(root->right, user_free);
    }
    
    if (root->udata && user_free)
        user_free(root->udata);
    
    generic_free(root);
}

int bvh_inside(BVHNode *node, float x, float y, float z)
{
    return is_aabb3_contains_point_ub(&node->bbox, x, y, z);
}

BVHNode *bvh_query_r(BVHNode *root, float x, float y, float z)
{
    if (bvh_inside(root, x, y, z))
    {
        if (root->axis != BVH_LEAF)
        {
            BVHNode *node = bvh_query(root->left, x, y, z);
            
            if (node)
                return node;
                
            node = bvh_query(root->right, x, y, z);
            if (node)
                return node;
        }
        
        return root;
    }
    
    return NULL;
}

#define LEVEL_MAX 8

BVHNode *bvh_query_l(BVHNode *root, float x, float y, float z)
{
	BVHNode *stack[LEVEL_MAX];
	int level = 0;

	while (root)
	{
		if (bvh_inside(root, x, y, z))
		{
			if (root->axis == BVH_LEAF)
				break;

			if (level == LEVEL_MAX)
				break; /* !BVH_LEAF */

			stack[level++] = root->right;
			root = root->left;
		}
		else if (level > 0)
			root = stack[--level];
		else
			root = NULL;
	}

	return root;
}

BVHNode *bvh_query(BVHNode *root, float x, float y, float z)
{
	return bvh_query_l(root, x, y, z);
}
