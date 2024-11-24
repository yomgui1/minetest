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

#include <math.h>

#include "geometry.h"

#define IS_AABB3_CONTAIN_FUNC(type_short) \
    int is_aabb3_contains_point_##type_short(AABB3##type_short *aabb, float x, float y, float z) \
    { return (x >= (float)aabb->min_x) && \
		(x <= (float)aabb->max_x) && \
		(y >= (float)aabb->min_y) && \
		(y <= (float)aabb->max_y) && \
		(z >= (float)aabb->min_z) && \
		(z <= (float)aabb->max_z); }

IS_AABB3_CONTAIN_FUNC(ub);
IS_AABB3_CONTAIN_FUNC(i);
IS_AABB3_CONTAIN_FUNC(f);

#define GET_AABB3_VERTEX_FUNC(type_short) \
    void get_aabb3_vertex_##type_short(AABB3##type_short *aabb, int i, float *x, float *y, float *z)\
    {\
        switch (i)\
        {\
            case 0: *x = aabb->min_x; *y = aabb->min_y; *z = aabb->min_z; break;\
            case 1: *x = aabb->min_x; *y = aabb->min_y; *z = aabb->max_z; break;\
            case 2: *x = aabb->min_x; *y = aabb->max_y; *z = aabb->min_z; break;\
            case 3: *x = aabb->min_x; *y = aabb->max_y; *z = aabb->max_z; break;\
            case 4: *x = aabb->max_x; *y = aabb->min_y; *z = aabb->min_z; break;\
            case 5: *x = aabb->max_x; *y = aabb->min_y; *z = aabb->max_z; break;\
            case 6: *x = aabb->max_x; *y = aabb->max_y; *z = aabb->min_z; break;\
            case 7: *x = aabb->max_x; *y = aabb->max_y; *z = aabb->max_z; break;\
        }\
    }

GET_AABB3_VERTEX_FUNC(ub);
GET_AABB3_VERTEX_FUNC(i);
GET_AABB3_VERTEX_FUNC(f);

#define GET_AABB3_SPHERE_FUNC(type_short) \
    void get_aabb3_sphere_##type_short(AABB3##type_short *aabb, BSphere *bsphere)\
    {\
        float _x, _y, _z;\
        _x = aabb->max_x - aabb->min_x;\
        _y = aabb->max_y - aabb->min_y;\
        _z = aabb->max_z - aabb->min_z;\
        bsphere->x = _x / 2.0 + aabb->min_x;\
        bsphere->y = _y / 2.0 + aabb->min_y;\
        bsphere->z = _z / 2.0 + aabb->min_z;\
        bsphere->d = sqrtf(_x*_x + _y*_y + _z*_z);\
    }

GET_AABB3_SPHERE_FUNC(ub);
GET_AABB3_SPHERE_FUNC(i);
GET_AABB3_SPHERE_FUNC(f);

void normalize_plane(float plane[4])
{
    float magnitude;

	magnitude = plane[0]*plane[0] + plane[1]*plane[1] + plane[2]*plane[2];
	magnitude = sqrtf(magnitude);

    plane[0] /= magnitude;
    plane[1] /= magnitude;
    plane[2] /= magnitude;
    plane[3] /= magnitude;
}

void translate_frustum_planes(frustumPlanes *src, frustumPlanes *dst,
							  float dx, float dz)
{

    dst->left[0] = src->left[0];
    dst->left[1] = src->left[1];
    dst->left[2] = src->left[2];
    dst->left[3] = src->left[3] + dx;
    normalize_plane(dst->left);

    dst->right[0] = src->right[0];
    dst->right[1] = src->right[1];
    dst->right[2] = src->right[2];
    dst->right[3] = src->right[3] - dx;
    normalize_plane(dst->right);

    dst->top[0] = src->top[0];
    dst->top[1] = src->top[1];
    dst->top[2] = src->top[2];
    dst->top[3] = src->top[3];
    normalize_plane(dst->top);

    dst->bottom[0] = src->bottom[0];
    dst->bottom[1] = src->bottom[1];
    dst->bottom[2] = src->bottom[2];
    dst->bottom[3] = src->bottom[3];
    normalize_plane(dst->bottom);

    dst->far[0] = src->far[0];
    dst->far[1] = src->far[1];
    dst->far[2] = src->far[2];
    dst->far[3] = src->far[3] - dz;
    normalize_plane(dst->far);

    dst->near[0] = src->near[0];
    dst->near[1] = src->near[1];
    dst->near[2] = src->near[2];
    dst->near[3] = src->near[3] + dz;
    normalize_plane(dst->near);
}

float frustum_point_distance(float plane[4], float x, float y, float z)
{
    return plane[0] * x + plane[1] * y + plane[2] * z + plane[3];
}

HalfSpace classify_point(float plane[4], float x, float y, float z)
{
    float d = frustum_point_distance(plane, x, y, z);

    if (d > 0) return HALFSPACE_POSITIVE;
    if (d < 0) return HALFSPACE_NEGATIVE;
    return HALFSPACE_ON_PLANE;
}

frustumSpace point_inside_frustum(frustumPlanes *planes,
								  float x, float y, float z)
{
    HalfSpace hs;

    hs = classify_point(planes->left, x, y, z);
    if (hs == HALFSPACE_NEGATIVE) return frustum_OUTSIDE;
    if (hs == HALFSPACE_POSITIVE)
    {
        hs = classify_point(planes->right, x, y, z);
        if (hs == HALFSPACE_NEGATIVE) return frustum_OUTSIDE;
        if (hs == HALFSPACE_POSITIVE)
        {
            hs = classify_point(planes->top, x, y, z);
            if (hs == HALFSPACE_NEGATIVE) return frustum_OUTSIDE;
            if (hs == HALFSPACE_POSITIVE)
            {
                hs = classify_point(planes->bottom, x, y, z);
                if (hs == HALFSPACE_NEGATIVE) return frustum_OUTSIDE;
                if (hs == HALFSPACE_POSITIVE)
                {
                    hs = classify_point(planes->far, x, y, z);
                    if (hs == HALFSPACE_NEGATIVE) return frustum_OUTSIDE;
                    if (hs == HALFSPACE_POSITIVE)
                    {
                        hs = classify_point(planes->near, x, y, z);
                        if (hs == HALFSPACE_NEGATIVE) return frustum_OUTSIDE;
                        if (hs == HALFSPACE_POSITIVE)
                            return frustum_INSIDE;
                        else /* on near plane */
                            return frustum_ON_PLANE;
                    }
                    else /* on far plane */
                        return frustum_ON_PLANE;
                }
                else /* on bottom plane */
                {
                    hs = classify_point(planes->far, x, y, z);
                    if (hs == HALFSPACE_NEGATIVE) return frustum_OUTSIDE;
                    hs = classify_point(planes->near, x, y, z);
                    if (hs == HALFSPACE_NEGATIVE) return frustum_OUTSIDE;
                    return frustum_ON_PLANE;
                }
            }
            else /* on top plane */
            {
                hs = classify_point(planes->far, x, y, z);
                if (hs == HALFSPACE_NEGATIVE) return frustum_OUTSIDE;
                hs = classify_point(planes->near, x, y, z);
                if (hs == HALFSPACE_NEGATIVE) return frustum_OUTSIDE;
                return frustum_ON_PLANE;
            }
        }
        else /* on right plane */
        {
            hs = classify_point(planes->top, x, y, z);
            if (hs == HALFSPACE_NEGATIVE) return frustum_OUTSIDE;
            hs = classify_point(planes->bottom, x, y, z);
            if (hs == HALFSPACE_NEGATIVE) return frustum_OUTSIDE;
            hs = classify_point(planes->far, x, y, z);
            if (hs == HALFSPACE_NEGATIVE) return frustum_OUTSIDE;
            hs = classify_point(planes->near, x, y, z);
            if (hs == HALFSPACE_NEGATIVE) return frustum_OUTSIDE;
            return frustum_ON_PLANE;
        }
    }

    /* on left plane */
    hs = classify_point(planes->top, x, y, z);
    if (hs == HALFSPACE_NEGATIVE) return frustum_OUTSIDE;
    hs = classify_point(planes->bottom, x, y, z);
    if (hs == HALFSPACE_NEGATIVE) return frustum_OUTSIDE;
    hs = classify_point(planes->far, x, y, z);
    if (hs == HALFSPACE_NEGATIVE) return frustum_OUTSIDE;
    hs = classify_point(planes->near, x, y, z);
    if (hs == HALFSPACE_NEGATIVE) return frustum_OUTSIDE;
    return frustum_ON_PLANE;
}

frustumSpace sphere_inside_frustum(frustumPlanes *planes,
								   BSphere *bsphere)
{
    float r = bsphere->d / 2.0;

#define SPHERE_INTERSECT_WITH_PLANE(p, x, y, z) ({ float _d;\
    _d = frustum_point_distance(p, x, y, z); \
    if (_d < -r) return frustum_OUTSIDE; \
    if (fabs(_d) < r) return frustum_INTERSECT; })

    SPHERE_INTERSECT_WITH_PLANE(planes->left, bsphere->x, bsphere->y, bsphere->z);
    SPHERE_INTERSECT_WITH_PLANE(planes->right, bsphere->x, bsphere->y, bsphere->z);
    SPHERE_INTERSECT_WITH_PLANE(planes->top, bsphere->x, bsphere->y, bsphere->z);
    SPHERE_INTERSECT_WITH_PLANE(planes->bottom, bsphere->x, bsphere->y, bsphere->z);
    SPHERE_INTERSECT_WITH_PLANE(planes->far, bsphere->x, bsphere->y, bsphere->z);
    SPHERE_INTERSECT_WITH_PLANE(planes->near, bsphere->x, bsphere->y, bsphere->z);

    return frustum_INSIDE;
}

frustumSpace aabb3_inside_frustum(frustumPlanes *planes,
								  float vertices[8][3])
{
    int j, i, insiders=0;
    float (*_planes)[4] = (void *)planes;

    /* Loop on planes */
    for (i=0; i < 6; i++)
    {
        int count=8;

        /* Loop on points */
        for (j=0; j < 8; j++)
        {
            if (classify_point(_planes[i], vertices[j][0], vertices[j][1], vertices[j][2]) == HALFSPACE_NEGATIVE)
                count--;
            else
                insiders++;
        }

        /* All points are on the wrong side of tested plane */
        if (count == 0)
            return frustum_OUTSIDE;
    }

    if (insiders == 8)
        return frustum_INSIDE;

    return frustum_INTERSECT;
}

frustumSpace aabb3ub_inside_frustum(frustumPlanes *planes, AABB3ub *bbox)
{
    int i;
    float vertices[8][3];

    for (i=0; i < 8; i++)
        get_aabb3_vertex_ub(bbox, i, &vertices[i][0], &vertices[i][1], &vertices[i][2]);

    return aabb3_inside_frustum(planes, vertices);
}

frustumSpace aabb3i_inside_frustum(frustumPlanes *planes, AABB3i *bbox)
{
    int i;
    float vertices[8][3];

    for (i=0; i < 8; i++)
        get_aabb3_vertex_i(bbox, i, &vertices[i][0], &vertices[i][1], &vertices[i][2]);

    return aabb3_inside_frustum(planes, vertices);
}

