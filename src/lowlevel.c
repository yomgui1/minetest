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

/* Lowlevel Python module to access and render map.
 *
 * -- About Map format --
 * To be compatible with user map, I've decided to organize my map as the genuine MC.
 * This is who beta 1.3 format handles map files:
 *
 * A map is a list of region files, named as "r.x.z.mcr" where x an z are region's coordinates.
 *   Each region is a group of 32x32 chunks (=1024 chunks/region).
 *   Region coordinates is the 1/32th of its chunk coordinates (chunk location / 32).
 *
 * A chunk is a group of 16x16x128 blocks organized as X.Z.Y (=32768 blocks/chunk).
 *   This is gives 33554432 blocks per regions, or a surface of 262144 blocks square.
 */

/* Includes */

#include <Python.h>
#include <structmember.h>

#ifdef __MORPHOS__
#include <tgl/gl.h>
#include <tgl/glut.h>
#else
#define GL_GLEXT_PROTOTYPES
#include <GL/gl.h>
#include <GL/glut.h>
#include <GL/glext.h>
#endif

#include <stdint.h>

#include "cluster.h"
#include "meshes.h"

#ifndef __MORPHOS__
#define dprintf printf
#endif

/* Python help macros */

#define INSI(m, s, v) if (PyModule_AddIntConstant(m, s, v)) return
#define INSS(m, s, v) if (PyModule_AddStringConstant(m, s, v)) return
#define INSL(m, s, v) \
  if (PyModule_AddObject(m, s, PyLong_FromUnsignedLong(v))) return

#define OBJ_TNAME(o) (((PyObject *)(o))->ob_type->tp_name)
#define ADD_TYPE(m, s, t) \
  {Py_INCREF(t); PyModule_AddObject(m, s, (PyObject *)(t));}

#define PyMeshObject_Check(op) PyObject_TypeCheck(op, &PyMeshObject_Type)
#define PyMeshObject_CheckExact(op) \
  (((PyObject *)(op))->ob_type == &PyMeshObject_Type)
#define PyClusterObject_Check(op) PyObject_TypeCheck(op, &PyClusterObject_Type)
#define PyClusterObject_CheckExact(op) \
  (((PyObject *)(op))->ob_type == &PyClusterObject_Type)

/* timestamp macros */

#ifdef __MORPHOS__
#define TIMESTAMP_AS_SECONDS(t) ((t)*4/133333333.)
#else
#define TIMESTAMP_AS_SECONDS(t) ((t)/980e6/4)
#endif

/* list management macros */

#define LIST_ADD_TAIL(l, n) do {				\
		(n)->previous = (l)->previous;			\
		(n)->next = NULL;						\
		(l)->previous->next = (n);				\
		(l)->previous = (n);					\
	} while (0);

#define LIST_ADD_HEAD(l, n) do {				\
		(n)->previous = NULL;					\
		(n)->next = (l)->next;					\
		(l)->next = (n);						\
	} while (0);

#define REMOVE(n) do {							\
	if ((n)->previous)							\
		(n)->previous->next = (n)->next;		\
	if ((n)->next)								\
		(n)->next->previous = (n)->previous;	\
	} while (0);

/* other help macros */

#define MIN(a,b) ({typeof(a) _a=(a); typeof(b) _b=(b); _a<_b ? _a:_b;})
#define MAX(a,b) ({typeof(a) _a=(a); typeof(b) _b=(b); _a>_b ? _a:_b;})
#define CLAMP(a,b,c) \
  ({typeof(a) _a=(a); typeof(b) _b=(b); typeof(c) _c=(c); \
	_b<_a ? _a:(_b>_c ? _c:_b);})
#define arraysize(a) (sizeof(a) / sizeof(typeof(a)))

/* internal engine rendering settings */

#define MAX_HIT_SQUARED_RANGE (5.*5.)
#define SELECTION_THICKNESS 2.5
#define SELECTION_OFFSET 0.01

/* rendering stuffs */

#define FOG_SIZE 20
#define FOG_DENSITY 1.f
#define MAX_RENDER_CELLS 8
#define BLOCK_PER_CELL_Y (CLUSTER_SIZE_Y/MAX_RENDER_CELLS)

#define SHOW_CLUSTER_STATS
#define CELL_CULLING

#define MAX_RENDERED_FACES 20000 //INT_MAX /* unlimited */

#define MAP_CELL(cells, x, y, z)							\
	((cells) [(x)>>WORLD_CLUSTER_X_SHIFT]					\
	 [(z)>>WORLD_CLUSTER_Z_SHIFT]							\
	 [(y)/BLOCK_PER_CELL_Y])
#define MAP_BLOCK_INFO(cells, x, y, z)						\
	(MAP_CELL(cells, x, y, z).blocks_info					\
	 [(x) & CLUSTER_SIZE_X_MASK]							\
	 [(z) & CLUSTER_SIZE_Z_MASK]							\
	 [(y) & (BLOCK_PER_CELL_Y-1)])
#define MAP_BLOCK_ID(cells, x, y, z) MAP_BLOCK_INFO(cells, x, y, z).id
#define MAP_BLOCK_OCCLUSION(cells, x, y, z)	(MAP_BLOCK_INFO(cells, x, y, z).occlusion)
#define MAP_BLOCK_SET_OCCLUSION(cells, x, y, z, f) (MAP_BLOCK_OCCLUSION(cells, x, y, z) |= (1<<(f)))

/*==== New types and definitions =============================================*/

struct PyMapObject_STRUCT;
struct PyNodeObject_STRUCT;

enum {
    FACE_BOTTOM=0,
    FACE_TOP,
    FACE_RIGHT,
    FACE_LEFT,
    FACE_FRONT,
    FACE_REAR,
};

typedef GLfloat VertexColors[4];

typedef enum MeshType {
    MESH_EMPTY=0,
    MESH_CUBE,
    MESH_CUBE2,
    MESH_PLANE,
    MESH_XPLANE,
    MESH_CROSS,
    MESH_TORCH,
    MESH_SLAB,
    MESH_STAIRS,
    MESH_PANE,
    MESH_STICKY,
    MESH_LEVER,
} MeshType;

typedef enum BlockID {
  BID_AIR=0,
  BID_END_WORLD=95,
} BlockID;

typedef struct PointData {
    GLfloat vertices[3];
    GLfloat texels[2];
} PointData;

typedef struct FaceData {
    PointData points[4];
    GLfloat tint[3]; /* Tint color per face */
} FaceData;

typedef struct RenderPointData {
    GLfloat vertices[3];
    GLfloat texels[2];
    GLfloat colors[4];
} RenderPointData;

typedef struct RenderFaceData {
    RenderPointData points[4];
} RenderFaceData;

typedef struct RenderingStats {
    double rendering_time;
    unsigned int visited_items;
    unsigned int drawn_items;
    unsigned int visited_subitems;
    unsigned int drawn_subitems;
} RenderingStats;

typedef int (*NodeFunc)(struct PyNodeObject_STRUCT *node);

typedef void (*LightingFunc)(struct PyNodeObject_STRUCT *node, int face_id,
							 VertexColors *colors);

/* OpenGL projection matrix */
typedef struct OGLProjMatrix {
    GLdouble _11, _21, _31, _41;
    GLdouble _12, _22, _32, _42;
    GLdouble _13, _23, _33, _43;
    GLdouble _14, _24, _34, _44;
} OGLProjMatrix;

/* Faces rendering list.
 * Works in append mode: easy to add more faces, but not to remove them.
 * Faces are rendered as a whole in one to render_faces_array().
 */
typedef struct RenderCell {
    RenderFaceData *faces;
	unsigned count;
	unsigned allocated_faces;
} RenderCell;

typedef struct MapCell {
	RenderCell static_faces;
	RenderCell blend_faces;
	BlockInfo blocks_info[CLUSTER_SIZE_X][CLUSTER_SIZE_Z][BLOCK_PER_CELL_Y];
	BSphere bsphere;
	uint8_t render;
} MapCell;

static GLfloat fog_planes[32*4*3];

#ifdef __MORPHOS__
struct Library *TinyGLBase = NULL;
extern GLContext *__tglContext;
#endif

/*==== Python Types definitions ==============================================*/

/* Mesh object describes a static mesh of faces */

typedef struct PyMeshObject_STRUCT
{
    PyObject_HEAD
    MeshType type;						/* mesh type : only MESH_CUBE supported yet */
    int texid;
    struct {
#if __BYTE_ORDER == __BIG_ENDIAN
        /* BIGENDIAN order */
        uint32_t pad:28;
        uint32_t level:1;			/* Top face should not be occulted if level node value is not 16 */
        uint32_t translucent:1;		/* Texture uses translucent colors, like water and lava (rendered in a second pass) */
        uint32_t ao:1;				/* AO ligthing pass requested */
        uint32_t alpha:1;			/* Texture is not fully opaque on the face but not translucent (like glass) */
#else
		uint32_t alpha:1;
        uint32_t ao:1;
        uint32_t translucent:1;
		uint32_t level:1;
#endif
    } flags;

	uint8_t occlusion;					/* bit set to indicate FACE_XXX that occlude others */
    NodeFunc occlusion_and_lighting;	/* Callback to do per faces occlusion and lighting on nodes associated to the mesh */
    unsigned int count;					/* number of faces */
    FaceData *faces;					/* Faces array of 'count' items */
} PyMeshObject;

typedef struct PyMapObject_STRUCT
{
	PyObject_HEAD
	PyMeshObject *meshes[256];
	MapCell cells[WORLD_CLUSTER_X][WORLD_CLUSTER_Z][MAX_RENDER_CELLS];
    RenderingStats stats;
	char fog_enabled;
} PyMapObject;

/* Camera object */
typedef struct PyCameraObject_STRUCT
{
    PyObject_HEAD
	float position[3];
    float direction[3];			/* MUST BE A NORMALIZED VECTOR */
    float sky[3];				/* MUST BE A NORMALIZED VECTOR */
    float aspect;				/* viewport aspect */
    float fov;					/* camera viewing angle */
    float fov_cos2;				/* squared cosinus of the cam_fov */
    float near, far;
    float range2, bias;
    float delta_c;
    float big_cos2;
    GLdouble projMat[16];
    GLdouble modelMat[16];
    GLdouble fogMat[16];
    GLint viewport[4];
    frustumPlanes frustum_planes;
	int dirty:1;
} PyCameraObject;

static PyTypeObject PyMeshObject_Type;
static PyTypeObject PyMapObject_Type;
static PyTypeObject PyCameraObject_Type;

/*==== Internal routines =====================================================*/

void * generic_malloc(size_t size)
{
    return PyMem_Malloc(size);
}

void generic_free(void *ptr)
{
    PyMem_Free(ptr);
}

/*---- statistics related functions ------------------------------------------*/

#if defined(__ppc__) || defined (__powerpc__)

#define READ_TIMESTAMP(var) ppc_getcounter(&var)

static void ppc_getcounter(uint64_t *v)
{
    register unsigned long tbu, tb, tbu2;

  loop:
    asm volatile ("mftbu %0" : "=r" (tbu) );
    asm volatile ("mftb  %0" : "=r" (tb)  );
    asm volatile ("mftbu %0" : "=r" (tbu2));
    if (__builtin_expect(tbu != tbu2, 0)) goto loop;

    /* The slightly peculiar way of writing the next lines is
       compiled better by GCC than any other way I tried.
     */

    ((long*)(v))[0] = tbu;
    ((long*)(v))[1] = tb;
}
#elif defined(__i386__)

#define READ_TIMESTAMP(val) \
  __asm__ __volatile__("rdtsc" : "=A" (val))

#elif defined(__x86_64__)

#define READ_TIMESTAMP(val) \
    __asm__ __volatile__("rdtsc" : \
                         "=a" (((int*)&(val))[0]), "=d" (((int*)&(val))[1]));


#else

#error "Don't know how to implement timestamp counter for this architecture"

#endif

/*---- rendering related functions -------------------------------------------*/

static void _use_texture(int tex_id)
{
	if (tex_id >= 0)
    {
        glEnable(GL_TEXTURE_2D);
        glBindTexture(GL_TEXTURE_2D, tex_id);
    }
    else
        glDisable(GL_TEXTURE_2D);
}

static void _enable_faces_render_states(void)
{
    glEnableClientState(GL_VERTEX_ARRAY);
    glEnableClientState(GL_COLOR_ARRAY);
    glEnableClientState(GL_TEXTURE_COORD_ARRAY);
    glEnable(GL_CULL_FACE);
}

static void _disable_faces_render_states(void)
{
    glDisableClientState(GL_VERTEX_ARRAY);
    glDisableClientState(GL_COLOR_ARRAY);
    glDisableClientState(GL_TEXTURE_COORD_ARRAY);
    glDisable(GL_CULL_FACE);
}

static void _enable_blend_faces_render(void)
{
	glDisable(GL_CULL_FACE);
	glEnable(GL_BLEND);
	//glDepthMask(GL_FALSE); /* disable depth writing, but keep depth testing! */
}

static void _disable_blend_faces_render(void)
{
	glEnable(GL_CULL_FACE);
	glDisable(GL_BLEND);
	//glDepthMask(GL_TRUE);
}

static void render_faces_array(RenderFaceData *faces, unsigned int count,
							   int fog)
{
#if 0
    if (fog)
    {
        /* Fog emulation using texture mixing with primary color */
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_COMBINE);

        glTexEnvf(GL_TEXTURE_ENV, GL_COMBINE_ALPHA, GL_SUBTRACT);
        glTexEnvf(GL_TEXTURE_ENV, GL_COMBINE_RGB, GL_INTERPOLATE);

        glTexEnvf(GL_TEXTURE_ENV, GL_SOURCE0_RGB, GL_TEXTURE);
        glTexEnvf(GL_TEXTURE_ENV, GL_OPERAND0_RGB, GL_SRC_COLOR);

        glTexEnvf(GL_TEXTURE_ENV, GL_SOURCE1_RGB, GL_PRIMARY_COLOR);
        glTexEnvf(GL_TEXTURE_ENV, GL_OPERAND1_RGB, GL_SRC_ALPHA);

        glTexEnvf(GL_TEXTURE_ENV, GL_SOURCE2_RGB, GL_PRIMARY_COLOR);
        glTexEnvf(GL_TEXTURE_ENV, GL_OPERAND2_RGB, GL_SRC_COLOR);
    }
#endif

    glVertexPointer(3, GL_FLOAT, sizeof(RenderPointData), &faces[0].points[0].vertices[0]);
    glTexCoordPointer(2, GL_FLOAT, sizeof(RenderPointData), &faces[0].points[0].texels[0]);
    glColorPointer(4, GL_FLOAT, sizeof(RenderPointData), &faces[0].points[0].colors[0]);

    //glLockArraysEXT(0, count*4);
    glDrawArrays(GL_QUADS, 0, count*4);
    //glUnlockArraysEXT();

#if 0
    if (fog)
        glTexEnvf(GL_TEXTURE_ENV, GL_TEXTURE_ENV_MODE, GL_MODULATE);
#endif
}

static FaceData * _create_faces(int count, const GLfloat *vertices,
								GLfloat *tint_rgb, GLfloat *texels,
								int texels_size)
{
    FaceData *faces = NULL;
    int i, j;

    if (texels_size >= (count*4*2*sizeof(GLfloat)))
    {
        faces = PyMem_Malloc(sizeof(FaceData) * count);
        if (faces)
        {
            for (i=0; i < count; i++)
            {
                for (j=0; j < 4; j++)
                {
                    faces[i].points[j].texels[0] = texels[(i*4+j)*2+0];
                    faces[i].points[j].texels[1] = texels[(i*4+j)*2+1];
                    faces[i].points[j].vertices[0] = vertices[(i*4+j)*3+0];
                    faces[i].points[j].vertices[1] = vertices[(i*4+j)*3+1];
                    faces[i].points[j].vertices[2] = vertices[(i*4+j)*3+2];

                    if (tint_rgb)
                    {
                        faces[i].tint[0] = tint_rgb[i*3+0];
                        faces[i].tint[1] = tint_rgb[i*3+1];
                        faces[i].tint[2] = tint_rgb[i*3+2];
                    }
                    else
                    {
                        faces[i].tint[0] = 1.0;
                        faces[i].tint[1] = 1.0;
                        faces[i].tint[2] = 1.0;
                    }
                }
            }
        }
        else
            PyErr_NoMemory();
    }
    else
		PyErr_Format(PyExc_TypeError, "texels array too small");

    return faces;
}

static int _is_point3D_renderable(float x, float y, float z,
								  PyCameraObject *camera)
{
    float dist, dot;

    /* position relative to the camera */
    x -= camera->position[0];
    y -= camera->position[1];
    z -= camera->position[2];

    /* 3D euclidian distance (squared) */
    dist = x*x + y*y + z*z;

    /* too close => render */
    if (dist <= 3*8*8)
        return 1;

    /* too far => not render */
    if (dist > camera->range2)
        return 0;

	/* between */

	/* Finish me: renderable viewport volume is not a shere.
	 * Exactly it's a pyramide.
	 * But I wonder if adding more time to compute precisely
	 * will not take more time than just compute «false» results.
	 */

    /* 3D dot + bias */
    dot  = camera->direction[0] * x;
	dot += camera->direction[1] * y;
	dot += camera->direction[2] * z;
    //dot += camera->bias;

    /* check if location in view FOV */
    if ((dot * dot / dist) < camera->big_cos2)
        return 0;

    /* remove back clusters */
    if (dot < 0.)
        return 0;

    return 1;
}

static void _frustum_planes_from_oglmatrix(frustumPlanes *planes,
										   OGLProjMatrix *projMat)

{
    planes->left[0]     = projMat->_41 + projMat->_11;
    planes->left[1]     = projMat->_42 + projMat->_12;
    planes->left[2]     = projMat->_43 + projMat->_13;
    planes->left[3]     = projMat->_44 + projMat->_14;

    normalize_plane(planes->left);

    planes->right[0]    = projMat->_41 - projMat->_11;
    planes->right[1]    = projMat->_42 - projMat->_12;
    planes->right[2]    = projMat->_43 - projMat->_13;
    planes->right[3]    = projMat->_44 - projMat->_14;

    normalize_plane(planes->right);

    planes->top[0]      = projMat->_41 - projMat->_21;
    planes->top[1]      = projMat->_42 - projMat->_22;
    planes->top[2]      = projMat->_43 - projMat->_23;
    planes->top[3]      = projMat->_44 - projMat->_24;

    normalize_plane(planes->top);

    planes->bottom[0]   = projMat->_41 + projMat->_21;
    planes->bottom[1]   = projMat->_42 + projMat->_22;
    planes->bottom[2]   = projMat->_43 + projMat->_23;
    planes->bottom[3]   = projMat->_44 + projMat->_24;

    normalize_plane(planes->bottom);

    planes->far[0]      = projMat->_41 - projMat->_31;
    planes->far[1]      = projMat->_42 - projMat->_32;
    planes->far[2]      = projMat->_43 - projMat->_33;
    planes->far[3]      = projMat->_44 - projMat->_34;

    normalize_plane(planes->far);

    planes->near[0]     = projMat->_41 + projMat->_31;
    planes->near[1]     = projMat->_42 + projMat->_32;
    planes->near[2]     = projMat->_43 + projMat->_33;
    planes->near[3]     = projMat->_44 + projMat->_34;

    normalize_plane(planes->near);
}

static void _camera_setup(PyCameraObject *camera, int flat)
{
    /* Setup Perspective matrix */
    glMatrixMode(GL_PROJECTION);

    if (flat)
    {
        glLoadIdentity();
        float d = camera->far + 5;
        glOrtho(-d*camera->aspect, d*camera->aspect, -d, d, .1, 1000.);
    }
    else
        glLoadMatrixd(camera->projMat);

    /* Setup Model matrix */
    glMatrixMode(GL_MODELVIEW);

    if (flat)
    {
        glLoadIdentity();
        gluLookAt(camera->position[0], 1.0, camera->position[2],
                  camera->position[0], 0.0, camera->position[2],
                  0.0, 0.0, 1.0);
    }
    else
        glLoadMatrixd(camera->modelMat);
}

static void _camera_update(PyCameraObject *camera)
{
    /* NOTE: this procedure changes Projection and Model matrices */
    OGLProjMatrix mat;

    camera->fov_cos2 = cos(camera->fov*0.7072);
    camera->fov_cos2 *= camera->fov_cos2;
    camera->range2 = camera->far * camera->far;

    glGetIntegerv(GL_VIEWPORT, camera->viewport);
    camera->aspect = (float)camera->viewport[2] / camera->viewport[3];

    /* Setup Perspective matrix */
    glMatrixMode(GL_PROJECTION);
    glLoadIdentity();
    gluPerspective(camera->fov * 180 / (camera->aspect*M_PI),
				   camera->aspect, camera->near, camera->far);
    glGetDoublev(GL_PROJECTION_MATRIX, camera->projMat);

    /* Setup Model matrix */
    glMatrixMode(GL_MODELVIEW);

    /* Store the fog model matrix */
    glLoadIdentity();
    gluLookAt(0, 0, -camera->far, 0, 0, 1, 0, 1, 0);
    glGetDoublev(GL_MODELVIEW_MATRIX, camera->fogMat);

    /* Then the general model matrix */
    glLoadIdentity();
    gluLookAt(camera->position[0], camera->position[1], camera->position[2],
              camera->position[0] + camera->direction[0],
              camera->position[1] + camera->direction[1],
              camera->position[2] + camera->direction[2],
              0.0, 1.0, 0.0);
    glGetDoublev(GL_MODELVIEW_MATRIX, camera->modelMat);

    /* Transform projection matrix by applying model transform matrix */
    glLoadMatrixd(camera->projMat);
    glMultMatrixd(camera->modelMat);

	/* fetch OGL matrix and fill our fustrum planes */
    glGetDoublev(GL_MODELVIEW_MATRIX, (GLdouble *)&mat);
    _frustum_planes_from_oglmatrix(&camera->frustum_planes, &mat);

	camera->dirty = 1;
}

static int _add_face(RenderCell *cell, PyMeshObject *mesh, int face_id,
					 unsigned x, unsigned y, unsigned z)
{
    int i;

    /* allocations are done by bunch of 16 faces */
    if (cell->count == cell->allocated_faces) {
        cell->allocated_faces += 16;
        cell->faces = realloc(cell->faces, cell->allocated_faces * sizeof(*cell->faces));
        if (!cell->faces) {
            PyErr_NoMemory();
            return -1;
        }
    }

    RenderFaceData *face = &cell->faces[cell->count++];
    FaceData *mesh_face = &mesh->faces[face_id];
    float base_light;

    /* Per face lighting */
    if (mesh->type == MESH_CUBE)
    {
        if (face_id == FACE_LEFT || face_id == FACE_RIGHT)
            base_light = 0.5;
        else
            base_light = 0.8;
    }
    else
        base_light = 0.8;

    /* Duplicate base faces data from mesh and adjust position and light */
    for (i=0; i < 4; i++)
    {
        face->points[i].vertices[0] = x + mesh_face->points[i].vertices[0];
        face->points[i].vertices[1] = y + mesh_face->points[i].vertices[1];
        face->points[i].vertices[2] = z + mesh_face->points[i].vertices[2];
        face->points[i].texels[0] = mesh_face->points[i].texels[0];
        face->points[i].texels[1] = mesh_face->points[i].texels[1];
        face->points[i].colors[0] = base_light;
        face->points[i].colors[1] = base_light;
        face->points[i].colors[2] = base_light;
        face->points[i].colors[3] = 1.;
    }
    return 0;
}

static void _faces_occlusion(PyMapObject *map, int fid, int fid_other,
							 BlockInfo *bi, BlockInfo *bi_other)
{
	PyMeshObject *mesh = map->meshes[bi->id];
	if (!mesh)
		return;
	PyMeshObject *mesh_other = map->meshes[bi_other->id];
	if (!mesh_other)
		return;
	if ((!mesh->flags.alpha && (mesh->occlusion & (1 << fid))) ||
		(mesh->flags.alpha && mesh_other->flags.alpha))
	{
		bi_other->occlusion |= 1 << fid_other;
	}
}

static void _do_block_occlusion(PyMapObject *map, BlockInfo *bi,
								unsigned x, unsigned y, unsigned z)
{
	/* World's end occlusion */
	if (y == 0)
		bi->occlusion |= 1 << FACE_BOTTOM;

	if (y == BLOCK_COUNT_Y-1)
		bi->occlusion |= 1 << FACE_TOP;

	if (z == 0)
		bi->occlusion |= 1 << FACE_REAR;

	if (z == BLOCK_COUNT_Z-1)
		bi->occlusion |= 1 << FACE_FRONT;

	if (x == 0)
		bi->occlusion |= 1 << FACE_RIGHT;

	if (x == BLOCK_COUNT_X-1)
		bi->occlusion |= 1 << FACE_LEFT;

	/* Per face occlusion */
	if (y > 0)
		_faces_occlusion(map, FACE_BOTTOM, FACE_TOP, bi,
						 &MAP_BLOCK_INFO(map->cells,x, y-1, z));

	if (y < (BLOCK_COUNT_Y-1))
		_faces_occlusion(map, FACE_TOP, FACE_BOTTOM, bi,
						 &MAP_BLOCK_INFO(map->cells, x, y+1, z));

	if (z > 0)
		_faces_occlusion(map, FACE_REAR, FACE_FRONT, bi,
						 &MAP_BLOCK_INFO(map->cells, x, y, z-1));

	if (z < (BLOCK_COUNT_Z-1))
		_faces_occlusion(map, FACE_FRONT, FACE_REAR, bi,
						 &MAP_BLOCK_INFO(map->cells, x, y, z+1));

	if (x > 0)
		_faces_occlusion(map, FACE_RIGHT, FACE_LEFT, bi,
						 &MAP_BLOCK_INFO(map->cells, x-1, y, z));

	if (x < (BLOCK_COUNT_X-1))
		_faces_occlusion(map, FACE_LEFT, FACE_RIGHT, bi,
						 &MAP_BLOCK_INFO(map->cells, x+1, y, z));
}

static void _set_block_id(PyMapObject *map, uint8_t id,
						  unsigned x, unsigned y, unsigned z)
{
	BlockInfo *bi = &MAP_BLOCK_INFO(map->cells, x, y, z);
	bi->id = id;
}

static size_t _render_cell(RenderCell *rc, PyCameraObject *camera,
						size_t rendered_faces)
{
	size_t to_render = 0;

	/* stop further rendering if max faces is reach */
	if (rendered_faces > MAX_RENDERED_FACES)
		return 0;

	to_render = MIN(rc->count, MAX_RENDERED_FACES - rendered_faces);
	render_faces_array(rc->faces, to_render, 0);

	return to_render;
}

/*============================================================================*/
/*==== PyMeshObject ==========================================================*/
/*----------------------------------------------------------------------------*/

static PyMeshObject * mesh_new(PyTypeObject *type, PyObject *args)
{
    PyMeshObject *self;
    MeshType mesh_type;
    Py_ssize_t texels_size, tint_rgb_size;
    GLfloat *texels, *tint_rgb=NULL;
    FaceData *faces;
    int i, j, count, texid;
    NodeFunc occ_light = NULL;

    if (!PyArg_ParseTuple(args, "Iis#|s#", &mesh_type, &texid, &texels,
						  &texels_size, &tint_rgb, &tint_rgb_size)) /* BR */
        return NULL;

#define MAKE_FACES(array) \
    count = sizeof(array) / (4*3*sizeof(typeof(array[0]))); \
    faces = _create_faces(count, array, tint_rgb, texels, texels_size); \

#define MAKE_FACES_X(array, f) MAKE_FACES(array); occ_light = f;

    switch (mesh_type) {
	case MESH_EMPTY     : count=0; faces = NULL; break;
	case MESH_CUBE      : MAKE_FACES(cube_vertices); break;
	case MESH_CUBE2     : MAKE_FACES(cube2_vertices); break;
	case MESH_STICKY    : MAKE_FACES(sticky_vertices); break;
	case MESH_SLAB      : MAKE_FACES(slab_vertices); break;
	case MESH_PLANE     : MAKE_FACES(plane_vertices); break;
	case MESH_XPLANE    : MAKE_FACES(xplane_vertices); break;
	case MESH_CROSS     : MAKE_FACES(cross_vertices); break;
	case MESH_TORCH     : MAKE_FACES(torch_vertices); break;
	case MESH_STAIRS    : MAKE_FACES(stairs_vertices); break;
	case MESH_LEVER     : MAKE_FACES(lever_vertices); break;
	case MESH_PANE: // like a cube but scaled in one axis
		MAKE_FACES(cube_vertices);
		// FIXME: scaling is wrong
		/* rescale all faces */
		for (i=0; i < count; i++) {
			/* Loop on vertices */
			for (j=0; j < 4; j++) {
				faces[i].points[j].vertices[2] *= 2*TEXEL_OFF;
			}
		}
		break;
	default:
		return (void *)PyErr_Format(PyExc_ValueError,
									"unknown mesh type %u",
									mesh_type);
    }

    if ((mesh_type != MESH_EMPTY) && !faces)
        return NULL;

    self = (PyMeshObject *)type->tp_alloc(type, 0); /* NR */
    if (NULL != self)
    {
        self->faces = faces;
        self->type = mesh_type;
        self->count = count;
        self->flags.translucent = 0;
        self->flags.alpha = 0;
        self->flags.ao = 1;
        self->flags.level = 0;
        self->texid = texid;
        self->occlusion_and_lighting = occ_light;
		self->occlusion = 0;
    }

    return self;
}

static void mesh_dealloc(PyMeshObject *self)
{
    if (self->faces)
        PyMem_Free(self->faces);

    ((PyObject *)self)->ob_type->tp_free((PyObject *)self);
}

static PyObject * mesh_get_flags(PyMeshObject *self, void *enclosure)
{
    unsigned int shift = (Py_uintptr_t)enclosure;

    if (*((unsigned int *)&self->flags) & (1 << shift))
        Py_RETURN_TRUE;
    Py_RETURN_FALSE;
}

static int mesh_set_flags(PyMeshObject *self, PyObject *value, void *enclosure)
{
    unsigned int shift = (Py_uintptr_t)enclosure;
    int res;

    res = PyObject_IsTrue(value);
    if (res < 0)
        return -1;

    if (res)
        *((unsigned int *)&self->flags) |= 1 << shift;
    else
        *((unsigned int *)&self->flags) &= ~(1 << shift);

    return 0;
}

static struct PyMethodDef mesh_methods[] = {
    {NULL} /* sentinel */
};

static PyMemberDef mesh_members[] = {
    {"texid", T_INT, offsetof(PyMeshObject, texid), 0, NULL},
    {"count", T_UINT, offsetof(PyMeshObject, count), RO, NULL},
	{"occlusion", T_UBYTE, offsetof(PyMeshObject, occlusion), 0, NULL},
	{"type", T_UINT, offsetof(PyMeshObject, type), RO, NULL},
    {NULL} /* sentinel */
};

static PyGetSetDef mesh_getseters[] = {
    {"alpha", (getter)mesh_get_flags, (setter)mesh_set_flags, "True if texture uses alpha", (void*)0},
    {"ao", (getter)mesh_get_flags, (setter)mesh_set_flags, "True if AO pass used", (void*)1},
    {"translucent", (getter)mesh_get_flags, (setter)mesh_set_flags, "True if mesh's texture has translucent alpha values", (void*)2},
    {"level", (getter)mesh_get_flags, (setter)mesh_set_flags, "True if node level value is used", (void*)3},
    {NULL} /* sentinel */
};

static PyTypeObject PyMeshObject_Type = {
    PyObject_HEAD_INIT(NULL)

    tp_name         : "lowlevel.Mesh",
    tp_basicsize    : sizeof(PyMeshObject),
    tp_flags        : Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    tp_doc          : "Mesh Objects",

    tp_new          : (newfunc)mesh_new,
    tp_dealloc      : (destructor)mesh_dealloc,
    tp_methods      : mesh_methods,
    tp_members      : mesh_members,
    tp_getset       : mesh_getseters,
};

/*==== PyMapObject ===========================================================*/

static PyMapObject * map_new(PyTypeObject *type)
{
    PyMapObject *self;

    self = (PyMapObject *)type->tp_alloc(type, 0);
    if (self)
    {
        bzero(self->meshes, sizeof(self->meshes));
		//bzero(self->cells, sizeof(self->cells));
		
		int cx, cy, cz;
		for (cx = 0; cx < WORLD_CLUSTER_X; cx++)
		{
			for (cz = 0; cz < WORLD_CLUSTER_Z; cz++)
			{
				for (cy = 0; cy < MAX_RENDER_CELLS; cy++)
				{
					MapCell *mc = &self->cells[cx][cz][cy];
					bzero(mc, sizeof(mc));
					mc->bsphere.x = (cx << WORLD_CLUSTER_X_SHIFT) + CLUSTER_SIZE_X / 2;
					mc->bsphere.y = cy * BLOCK_PER_CELL_Y + BLOCK_PER_CELL_Y / 2;
					mc->bsphere.z = (cz << WORLD_CLUSTER_Z_SHIFT) + CLUSTER_SIZE_Z / 2;
					mc->bsphere.d = 27.72; /* sqrt(3) * 16 */
				}
			}
		}
        self->fog_enabled = 0;
    }

    return self;
}

static int map_traverse(PyMapObject *self, visitproc visit, void *arg)
{
    int i;
    for (i=0; i < 256; i++)
        Py_VISIT(self->meshes[i]);
    return 0;
}

static int map_clear(PyMapObject *self)
{
    int i;
    for (i=0; i < 256; i++)
        Py_CLEAR(self->meshes[i]);
    return 0;
}

static void map_dealloc(PyMapObject *self)
{
	PyObject_GC_UnTrack(self);
    map_clear(self);
    ((PyObject *)self)->ob_type->tp_free((PyObject *)self);
}

static PyObject * map_clip_vector(PyMapObject *self, PyObject *args)
{
    float x, y, z; /* real vector, not block position */
    //short bx, by, bz;

    if (!PyArg_ParseTuple(args, "fff", &x, &y, &z))
        return NULL;

    //bx = (int)(x + .5);
    //by = (int)(y + .5);
    //bz = (int)(z + .5);

    return Py_BuildValue("fff", x, y, z);
}

static PyObject * map_has_mesh(PyMapObject *self, PyObject *args)
{
    uint8_t idx;
    PyMeshObject *mesh;

    if (!PyArg_ParseTuple(args, "B", &idx))
        return NULL;

    mesh = self->meshes[idx];
    if (mesh)
        Py_RETURN_TRUE;
    Py_RETURN_FALSE;
}

static PyObject * map_get_mesh(PyMapObject *self, PyObject *args)
{
    uint8_t idx;
    PyMeshObject *mesh;

    if (!PyArg_ParseTuple(args, "B", &idx))
        return NULL;

    mesh = self->meshes[idx];
    if (mesh)
    {
        Py_INCREF(mesh);
        return (PyObject *)mesh;
    }

    Py_RETURN_NONE;
}

static PyObject * map_set_mesh(PyMapObject *self, PyObject *args)
{
    uint8_t idx;
    PyMeshObject *mesh;

    if (!PyArg_ParseTuple(args, "BO!", &idx, &PyMeshObject_Type, &mesh))
        return NULL;

    Py_XDECREF(self->meshes[idx]);
    self->meshes[idx] = mesh;
    Py_INCREF(mesh);

    Py_RETURN_NONE;
}

static PyObject * map_get_blockid(PyMapObject *self, PyObject *args)
{
    unsigned int x, y, z;

    if (!PyArg_ParseTuple(args, "III", &x, &y, &z))
        return NULL;

	if (y >= BLOCK_COUNT_Y || z >= BLOCK_COUNT_Z || x >= BLOCK_COUNT_X)
        return PyErr_Format(PyExc_ValueError, "coordinates out of world range");

    return Py_BuildValue("B", MAP_BLOCK_ID(self->cells, x, y, z));
}

static PyObject * map_set_blockid(PyMapObject *self, PyObject *args)
{
	unsigned char id;
	unsigned int x, y, z;

    if (!PyArg_ParseTuple(args, "BIII", &id, &x, &y, &z))
        return NULL;

   if (y >= BLOCK_COUNT_Y || z >= BLOCK_COUNT_Z || x >= BLOCK_COUNT_X)
        return PyErr_Format(PyExc_ValueError, "coordinates out of world range");

	MAP_BLOCK_ID(self->cells, x, y, z) = id;
	Py_RETURN_NONE;
}

static PyObject * map_add_face(PyMapObject *self, PyObject *args)
{
    PyMeshObject *mesh;
    unsigned char face_id;
	unsigned int x, y, z;

    if (!PyArg_ParseTuple(args, "O!BIII", &PyMeshObject_Type, &mesh, &face_id,
                          &x, &y, &z))
        return NULL;

	if (y >= BLOCK_COUNT_Y || z >= BLOCK_COUNT_Z || x >= BLOCK_COUNT_X)
        return PyErr_Format(PyExc_ValueError, "coordinates out of world range");

    //if (_add_face(self, mesh, face_id, x, y, z))
	//	return NULL;

	Py_RETURN_NONE;
}

static PyObject * map_add_blocks(PyMapObject *self, PyObject *args)
{
    PyByteArrayObject *buffer;
    uint8_t *data;
    Py_ssize_t length;
    unsigned int cx, cz, x, y, z;

    if (!PyArg_ParseTuple(args, "O!II", &PyByteArray_Type, &buffer, &cx, &cz))
        return NULL;

    data = PyByteArray_AS_STRING(buffer);

    if (cx >= WORLD_CLUSTER_X || cz >= WORLD_CLUSTER_Z)
		return PyErr_Format(PyExc_ValueError, "coordinates out of world range");

	for (x=0; x < CLUSTER_SIZE_X; x++)
	{
		for (z=0; z < CLUSTER_SIZE_Z; z++)
		{
			for (y=0; y < CLUSTER_SIZE_Y; y++, data++)
			{
				const unsigned wx = cx*WORLD_CLUSTER_X + x;
				const unsigned wz = cz*WORLD_CLUSTER_Z + z;
				_set_block_id(self, *data, wx, y, wz);
			}
		}
	}

    Py_RETURN_NONE;
}

static PyObject * map_do_occlusion(PyMapObject *self, PyObject *args)
{
    unsigned int x, y, z;

	for (x=0; x < BLOCK_COUNT_X; x++)
	{
		for (z=0; z < BLOCK_COUNT_Z; z++)
		{
			for (y=0; y < BLOCK_COUNT_Y; y++)
			{
				BlockInfo *bi = &MAP_BLOCK_INFO(self->cells, x, y, z);
				if (bi->id != BID_AIR)
					_do_block_occlusion(self, bi, x, y, z);
			}
		}
	}

    Py_RETURN_NONE;
}

static PyObject * map_generate_faces(PyMapObject *self, PyObject *args)
{
    unsigned x=0, y=0, z=0;
    unsigned long t1=0,t2=0;

	/* Loop on world's block ids */
	for (x = 0; x < BLOCK_COUNT_X; x++)
	{
		for (z = 0; z < BLOCK_COUNT_Z; z++)
		{
			for (y = 0; y < BLOCK_COUNT_Y; y++)
			{
				MapCell *mc = &MAP_CELL(self->cells, x, y, z);
				BlockInfo *bi = &mc->blocks_info[x&15][z&15][y&15];
				if (bi->id == BID_AIR)
					continue;

				PyMeshObject *mesh = self->meshes[bi->id];
				if (mesh && (mesh->type == MESH_CUBE))
				{
					RenderCell *rc;

					if (mesh->flags.alpha)
						rc = &mc->blend_faces;
					else
						rc = &mc->static_faces;

					t1 += 6;
					int i;
					for (i=0; i < 6; i++)
					{
						if ((bi->occlusion & (1<<i)) == 0)
						{ _add_face(rc, mesh, i, x, y, z); t2++; }
					}
				}
			}
		}
	}

	if (t1)
	{
		dprintf("faces=%lu/%lu (", t2, t1);
		float r = (float)t2 / t1;
		if (r < 0.1)
			dprintf("< 0.1%%)\n");
		else
			dprintf("%.1f%%)\n", r);
	}
	else
		dprintf("no faces!\n");

    return PyLong_FromUnsignedLong(t2);
}

static PyObject * map_render(PyMapObject *self, PyObject *args)
{
    PyCameraObject *camera;
    int terrain_tex_id;
    size_t total_faces;

    if (!PyArg_ParseTuple(args, "O!i",
                          &PyCameraObject_Type, &camera,
                          &terrain_tex_id))
        return NULL;

    /* Statistics reset */
    bzero(&self->stats, sizeof(self->stats));
    total_faces = 0;

    const float cx = camera->position[0];
    const float cy = camera->position[1];
    const float cz = camera->position[2];

    uint64_t t[2];
    READ_TIMESTAMP(t[0]);

    glShadeModel(GL_SMOOTH);
    //glShadeModel(GL_FLAT);
    glPushMatrix();

    _enable_faces_render_states();
    _use_texture(terrain_tex_id);

    /* Loop on all map's cell */
    int i;
    MapCell *cell = &self->cells[0][0][0];

#if 1
	/* draw solid static faces */
    for (i = 0; i < WORLD_CLUSTER_X*WORLD_CLUSTER_Z*MAX_RENDER_CELLS; i++, cell++)
    {
		if (!cell->static_faces.count)
			continue;

		if (camera->dirty)
			cell->render = _is_point3D_renderable(cell->bsphere.x, cell->bsphere.y, cell->bsphere.z, camera);

		if (cell->render)
			total_faces += _render_cell(&cell->static_faces, camera, total_faces);
    }

	/* draw translucent faces */
	_enable_blend_faces_render();
	cell = &self->cells[0][0][0];
    for (i = 0; i < WORLD_CLUSTER_X*WORLD_CLUSTER_Z*MAX_RENDER_CELLS; i++, cell++)
    {
		if (!cell->blend_faces.count)
			continue;

		if (cell->render)
			total_faces += _render_cell(&cell->blend_faces, camera, total_faces);
    }
	_disable_blend_faces_render();
#endif

    _disable_faces_render_states();

    glPopMatrix();
    glDisable(GL_TEXTURE_2D);
    glShadeModel(GL_FLAT);

    /* Statistics write */
    READ_TIMESTAMP(t[1]);

    self->stats.rendering_time = TIMESTAMP_AS_SECONDS(t[1]-t[0]);
    self->stats.drawn_subitems = total_faces;
    camera->dirty = 0;

    Py_RETURN_NONE;
}

static struct PyMethodDef map_methods[] = {
    {"render", (PyCFunction)map_render, METH_VARARGS, NULL},
    {"has_mesh", (PyCFunction)map_has_mesh, METH_VARARGS, NULL},
    {"get_mesh", (PyCFunction)map_get_mesh, METH_VARARGS, NULL},
    {"set_mesh", (PyCFunction)map_set_mesh, METH_VARARGS, NULL},
    {"get_blockid", (PyCFunction)map_get_blockid, METH_VARARGS, NULL},
    {"set_blockid", (PyCFunction)map_set_blockid, METH_VARARGS, NULL},
    {"clip_vector", (PyCFunction)map_clip_vector, METH_VARARGS, NULL},
	{"add_face", (PyCFunction)map_add_face, METH_VARARGS, NULL},
	{"add_blocks", (PyCFunction)map_add_blocks, METH_VARARGS, NULL},
	{"generate_faces", (PyCFunction)map_generate_faces, METH_NOARGS, NULL},
	{"do_occlusion", (PyCFunction)map_do_occlusion, METH_NOARGS, NULL},
    {NULL} /* sentinel */
};

static PyMemberDef map_members[] = {
    {"rendering_time", T_DOUBLE, offsetof(PyMapObject, stats.rendering_time), RO, NULL},
    {"visited_clusters", T_UINT, offsetof(PyMapObject, stats.visited_items), RO, NULL},
    {"visited_nodes", T_UINT, offsetof(PyMapObject, stats.visited_subitems), RO, NULL},
    {"drawn_clusters", T_UINT, offsetof(PyMapObject, stats.drawn_items), RO, NULL},
    {"drawn_faces", T_UINT, offsetof(PyMapObject, stats.drawn_subitems), RO, NULL},
    {"fog_enabled", T_UBYTE, offsetof(PyMapObject, fog_enabled), 0, NULL},
    {NULL} /* sentinel */
};

static PyTypeObject PyMapObject_Type = {
    PyObject_HEAD_INIT(NULL)

    tp_name         : "lowlevel.Map",
    tp_basicsize    : sizeof(PyMapObject),
    tp_flags        : Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE | Py_TPFLAGS_HAVE_GC,
    tp_doc          : "Map Objects",

    tp_new          : (newfunc)map_new,
    tp_dealloc      : (destructor)map_dealloc,
    tp_traverse     : (traverseproc)map_traverse,
    tp_clear        : (inquiry)map_clear,
    tp_methods      : map_methods,
    tp_members      : map_members,
};

/*==== PyCameraObject ========================================================*/

static int camera_init(PyCameraObject *self, PyObject *args)
{
    self->position[0] = 0.0;
    self->position[1] = 0.0;
    self->position[2] = 0.0;

    self->direction[0] = 0.0;
    self->direction[1] = 0.0;
    self->direction[2] = 1.0;

    self->fov = M_PI/2;
    self->fov_cos2 = cos(self->fov / 2.);
    self->fov_cos2 *= self->fov_cos2;

    self->near = 0.1; /* ReadOnly */
    self->far = 300.;
    self->bias = 1.5; /* empirical */

    return 0;
}

static PyObject * camera_update(PyCameraObject *self)
{
    _camera_update(self);
    Py_RETURN_NONE;
}

static PyObject * camera_setup(PyCameraObject *self, PyObject *args)
{
    int flat=0;

    if (!PyArg_ParseTuple(args, "|i", &flat))
        return NULL;

    _camera_setup(self, flat);

    Py_RETURN_NONE;
}

static PyObject * camera_get_position(PyCameraObject *self, void *enclosure)
{
    return Py_BuildValue("fff", self->position[0], self->position[1], self->position[2]);
}

static int camera_set_position(PyCameraObject *self, PyObject *value,
							   void *enclosure)
{
    if (value)
    {
        float x,y,z;

        if (PyArg_ParseTuple(value, "fff", &x, &y, &z) < 0)
            return -1;

        self->position[0] = x;
        self->position[1] = y;
        self->position[2] = z;
    }
    else
        bzero(self->position, sizeof(self->position));

    return 0;
}

static PyObject * camera_get_direction(PyCameraObject *self, void *enclosure)
{
    return Py_BuildValue("fff", self->direction[0], self->direction[1], self->direction[2]);
}

static int camera_set_direction(PyCameraObject *self, PyObject *value,
								void *enclosure)
{
    if (value)
    {
        float x,y,z,d;

        if (PyArg_ParseTuple(value, "fff", &x, &y, &z) < 0)
            return -1;

        /* normalize and store */
        d = sqrtf(x*x+y*y+z*z);
        self->direction[0] = x / d;
        self->direction[1] = y / d;
        self->direction[2] = z / d;
    }
    else
        bzero(self->direction, sizeof(self->direction));

    return 0;
}

static PyObject * camera_get_sky(PyCameraObject *self, void *enclosure)
{
    return Py_BuildValue("fff", self->sky[0], self->sky[1], self->sky[2]);
}

static int camera_set_sky(PyCameraObject *self, PyObject *value,
						  void *enclosure)
{
    if (value)
    {
        float x,y,z,d;

        if (PyArg_ParseTuple(value, "fff", &x, &y, &z) < 0)
            return -1;

        /* normalize and store */
        d = sqrtf(x*x+y*y+z*z);
        self->sky[0] = x/d;
        self->sky[1] = y/d;
        self->sky[2] = z/d;
    }
    else
        bzero(self->sky, sizeof(self->sky));

    return 0;
}

static struct PyMethodDef camera_methods[] = {
    {"update", (PyCFunction)camera_update, METH_NOARGS, NULL},
    {"setup", (PyCFunction)camera_setup, METH_VARARGS, NULL},
    {NULL} /* sentinel */
};

static PyMemberDef camera_members[] = {
    {"px", T_FLOAT, offsetof(PyCameraObject, position[0]), 0, NULL},
    {"py", T_FLOAT, offsetof(PyCameraObject, position[1]), 0, NULL},
    {"pz", T_FLOAT, offsetof(PyCameraObject, position[2]), 0, NULL},
    {"dx", T_FLOAT, offsetof(PyCameraObject, direction[0]), 0, NULL},
    {"dy", T_FLOAT, offsetof(PyCameraObject, direction[1]), 0, NULL},
    {"dz", T_FLOAT, offsetof(PyCameraObject, direction[2]), 0, NULL},
    {"sx", T_FLOAT, offsetof(PyCameraObject, sky[0]), 0, NULL},
    {"sy", T_FLOAT, offsetof(PyCameraObject, sky[1]), 0, NULL},
    {"sz", T_FLOAT, offsetof(PyCameraObject, sky[2]), 0, NULL},
    {"fov", T_FLOAT, offsetof(PyCameraObject, fov), 0, NULL},
    {"near", T_FLOAT, offsetof(PyCameraObject, near), RO, NULL},
    {"far", T_FLOAT, offsetof(PyCameraObject, far), 0, NULL},
    {"bias", T_FLOAT, offsetof(PyCameraObject, bias), 0, NULL},
    {NULL} /* sentinel */
};

static PyGetSetDef camera_getseters[] = {
    {"position", (getter)camera_get_position, (setter)camera_set_position, "tuple of 3 floats for the camera position point", NULL},
    {"direction", (getter)camera_get_direction, (setter)camera_set_direction, "tuple of 3 floats for the camera direction vector", NULL},
    {"sky", (getter)camera_get_sky, (setter)camera_set_sky, "tuple of 3 floats for the camera sky vector", NULL},
    {NULL} /* sentinel */
};

static PyTypeObject PyCameraObject_Type = {
    PyObject_HEAD_INIT(NULL)

    tp_name         : "lowlevel.Camera",
    tp_basicsize    : sizeof(PyCameraObject),
    tp_flags        : Py_TPFLAGS_DEFAULT | Py_TPFLAGS_BASETYPE,
    tp_doc          : "Camera Objects",

    tp_new          : (newfunc)PyType_GenericNew,
    tp_init         : (initproc)camera_init,
    tp_methods      : camera_methods,
    tp_members      : camera_members,
    tp_getset       : camera_getseters,
};

/*==== Module methods ========================================================*/

#ifdef __MORPHOS__
static PyObject *
ll_setup(PyObject *self, PyObject *args)
{
    if (!PyArg_ParseTuple(args, "kk", &TinyGLBase, &__tglContext))
        return NULL;
    //dprintf("LowLevel: [setup] Base=%p, Ctx=%p\n", TinyGLBase, __tglContext);
    Py_RETURN_NONE;
}
#endif

/*==== Module setup ==========================================================*/

static PyMethodDef methods[] = {
#ifdef __MORPHOS__
    {"setup", (PyCFunction)ll_setup, METH_VARARGS, NULL},
#endif
    {NULL} /* sentinel */
};

#ifdef __MORPHOS__
void PyMorphOS_TermModule(void)
{
    TinyGLBase = NULL;
    __tglContext = NULL;
}
#endif

PyMODINIT_FUNC
initlowlevel(void)
{
    PyObject *m;
    int i;

    dprintf("Internal structures size:\n"
            "PyMeshObject   : %lu\n"
            "PyMapObject    : %lu\n"
            "RenderFaceData : %lu\n"
			"MapCell        : %lu\n",
			sizeof(PyMeshObject), sizeof(PyMapObject), sizeof(RenderFaceData),
			sizeof(MapCell));

    for (i=0; i<16; i++)
    {
        float dist = -i*i*i/128.;

        fog_planes[i*4*3+0]  = -10000;
        fog_planes[i*4*3+1]  = -10000;
        fog_planes[i*4*3+2]  = dist;
        fog_planes[i*4*3+3]  = 10000;
        fog_planes[i*4*3+4]  = -10000;
        fog_planes[i*4*3+5]  = dist;
        fog_planes[i*4*3+6]  = 10000;
        fog_planes[i*4*3+7]  = 10000;
        fog_planes[i*4*3+8]  = dist;
        fog_planes[i*4*3+9]  = -10000;
        fog_planes[i*4*3+10] = 10000;
        fog_planes[i*4*3+11] = dist;
    }

    m = Py_InitModule("lowlevel", methods);
    if (NULL != m)
    {
        int error = 0;

        error |= PyType_Ready(&PyMeshObject_Type);
        error |= PyType_Ready(&PyCameraObject_Type);
        error |= PyType_Ready(&PyMapObject_Type);

        if (!error)
        {
            ADD_TYPE(m, "Mesh", &PyMeshObject_Type);
            ADD_TYPE(m, "Camera", &PyCameraObject_Type);
            ADD_TYPE(m, "Map", &PyMapObject_Type);

            INSI(m, "MESH_EMPTY", MESH_EMPTY);
            INSI(m, "MESH_CUBE", MESH_CUBE);
            INSI(m, "MESH_CUBE2", MESH_CUBE2);
            INSI(m, "MESH_SLAB", MESH_SLAB);
            INSI(m, "MESH_PLANE", MESH_PLANE);
            INSI(m, "MESH_XPLANE", MESH_XPLANE);
            INSI(m, "MESH_CROSS", MESH_CROSS);
            INSI(m, "MESH_TORCH", MESH_TORCH);
            INSI(m, "MESH_STAIRS", MESH_STAIRS);
            INSI(m, "MESH_PANE", MESH_PANE);
            INSI(m, "MESH_STICKY", MESH_STICKY);
            INSI(m, "MESH_LEVER", MESH_LEVER);
        }
    }
}

/*############################################################################*/
