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

#ifndef GEMOMETRY_H
#define GEMOMETRY_H

#include "stdint.h"

/* Axis Oriented Bounding Box in various space */

/* sizeof = 6 */
typedef struct AABB3ub {
    uint8_t min_x, max_x;
    uint8_t min_y, max_y;
    uint8_t min_z, max_z;
} AABB3ub;

/* sizeof = 24 */
typedef struct AABB3i {
    int32_t min_x, max_x;
    int32_t min_y, max_y;
    int32_t min_z, max_z;
} AABB3i;

/* sizeof = 24 */
typedef struct AABB3f {
    float min_x, max_x;
    float min_y, max_y;
    float min_z, max_z;
} AABB3f;

/* sizeof = 16 */
typedef struct BSphere {
    float x, y, z;		/* center */
    float d;			/* diameter */
} BSphere;

#define IS_AABB3_CONTAIN_PROTO(type_short) \
    int is_aabb3_contains_point_##type_short(AABB3##type_short *aabb, float x, float y, float z)

/* Following function return 0 if point is on BBox border, 1 if inside and -1 if outside */
IS_AABB3_CONTAIN_PROTO(ub);
IS_AABB3_CONTAIN_PROTO(i);
IS_AABB3_CONTAIN_PROTO(f);

#define GET_AABB3_VERTEX_PROTO(type_short) \
    void get_aabb3_vertex_##type_short(AABB3##type_short *aabb, int i, float *x, float *y, float *z)

GET_AABB3_VERTEX_PROTO(ub);
GET_AABB3_VERTEX_PROTO(i);
GET_AABB3_VERTEX_PROTO(f);

#define GET_AABB3_SPHERE_PROTO(type_short) \
    void get_aabb3_sphere_##type_short(AABB3##type_short *aabb, BSphere *bsphere)

GET_AABB3_SPHERE_PROTO(ub);
GET_AABB3_SPHERE_PROTO(i);
GET_AABB3_SPHERE_PROTO(f);

#define point_in_aabb_2d(x, y, xmin, xmax, ymin, ymax) \
	((x >= xmin) && (x <= xmax) && (y >= ymin) && (y <= ymax))

#define point_in_aabb_3d(x, y, z, xmin, xmax, ymin, ymax, zmin, zmax) \
	((x >= xmin) && (x <= xmax) && \
	 (y >= ymin) && (y <= ymax) && \
	 (z >= zmin) && (z <= zmax))

typedef struct frustumPlanes {
    float left[4];
    float right[4];
    float top[4];
    float bottom[4];
    float far[4];
    float near[4];
} frustumPlanes;

typedef enum HalfSpace {
    HALFSPACE_NEGATIVE,
    HALFSPACE_POSITIVE,
    HALFSPACE_ON_PLANE,
} HalfSpace;

typedef enum frustumSpace {
    frustum_OUTSIDE,
    frustum_INSIDE,
    frustum_ON_PLANE,
	frustum_INTERSECT=frustum_ON_PLANE,
} frustumSpace;

extern void normalize_plane(float plane[4]);
extern void translate_frustum_planes(frustumPlanes *src, frustumPlanes *dst,
									 float dx, float dz);
extern float frustum_point_distance(float plane[4], float x, float y, float z);
extern HalfSpace classify_point(float plane[4], float x, float y, float z);
extern frustumSpace point_inside_frustum(frustumPlanes *planes,
										 float x, float y, float z);
extern frustumSpace sphere_inside_frustum(frustumPlanes *planes,
										  BSphere *bsphere);
extern frustumSpace aabb3_inside_frustum(frustumPlanes *planes,
										 float vertices[8][3]);
extern frustumSpace aabb3ub_inside_frustum(frustumPlanes *planes,
										   AABB3ub *bbox);
extern frustumSpace aabb3i_inside_frustum(frustumPlanes *planes, AABB3i *bbox);

#endif
