from cgi import test
from gettext import translation
from os import name
import bpy
from mathutils import Euler, Vector, Quaternion
from math import *
import uuid
from bpy_extras import view3d_utils
import mathutils
import os
import bmesh

units_multiplier = 100

def euler_from_degrees(angles):
    x = radians(angles[0])
    y = radians(angles[1])
    z = radians(angles[2])

    return Euler((x, y, z))

def convert_in(coordinate):
    return coordinate / units_multiplier

def convert_out(coordinate):
    return coordinate * units_multiplier

def get_all_mesh_objects():
    return [obj for obj in bpy.data.objects if obj.type == 'MESH']

def get_visible_mesh_objects():
    return [obj for obj in bpy.data.objects if obj.type == 'MESH' and obj.visible_get()]

def get_selected_mesh_objects():
    return [obj for obj in bpy.data.objects if obj.type == 'MESH' and obj.select_get()]

def get_selected_objects():
    return [obj for obj in bpy.data.objects if obj.select_get()]

def get_unselected_objects():
    return [obj for obj in bpy.data.objects if not obj.select_get()]

def get_selected_and_visible_mesh_objects():
    return [obj for obj in bpy.data.objects if obj.type == 'MESH' and obj.select_get() and obj.visible_get()]

def get_objects_visible_in_camera(use_bounds=False):
    objects = []

    for obj in bpy.data.objects:
        if obj.type == 'MESH' and obj.visible_get():
            #Using Object Origin:
            
            if use_bounds:
                #Checking each point of bounding box:
                bounds = get_bounding_box(obj)
                for point in bounds:
                    if point_visible_in_any_region(bpy.context, point):
                        objects.append(obj)
                        continue
            else:
                if point_visible_in_any_region(bpy.context, obj.location):
                    objects.append(obj)

    return objects

def is_object_visible_camera(object):
    bounds = get_bounding_box(object)
    for point in bounds:
        if point_visible_in_any_region(bpy.context, point):
            return True
    return False


def get_reference_path(object):
    return bpy.path.abspath(object.data.library.filepath) if object.data.library else ''

def get_bounding_box(object):
    return [object.matrix_world @ mathutils.Vector(corner) for corner in object.bound_box]

def get_bounding_box_local(object):
    return [mathutils.Vector(corner) for corner in object.bound_box]

def get_size_bounds(object):
    bounds = get_bounding_box(object)

    min = bounds[0]
    max = bounds[6]

    return [max[0] - min[0], max[1] - min[1], max[2] - min[2]]

def min(points, axis):
    """Finds a point based on the smallest value of specified axis"""
    min = None

    for point in points:
        if min == None or point[axis] < min[axis]:
            min = point
            
    return min

def lerp(min, max, alpha):
    return min * (1 - alpha) + max * alpha

def average_positions(vectors):
    total = mathutils.Vector((0,0,0))

    for vector in vectors:
        total += vector
        
    return total / len(vectors)

def get_pivot(object):
    bounds = get_bounding_box_local(object)
    
    #Average position of bounding box is object center
    xy = average_positions(bounds)

    #set Z to the minimum of bounding box
    z = min(bounds, 2)
    
    return mathutils.Vector((xy[0], xy[1], z[2]))

def normal_to_euler(normal):
    return normal.to_track_quat('Z', 'Y').to_euler()

def set_origin(object, origin):
    """Set the pivot point of an object, using world space coordinate"""
    matrix_world = object.matrix_world
    offset = matrix_world.inverted() @ mathutils.Vector(origin)
    object.data.transform(mathutils.Matrix.Translation(-offset))
    matrix_world.translation = origin

def get_pivot_ws(object):
    return object.matrix_world @ get_pivot(object)

def get_transform(object):
    size = get_size_bounds(object)
    pivot = get_pivot_ws(object)

    size = convert_out(size)
    pivot = convert_out(size)

    return size, pivot 

def parent(parent_obj, child_obj):
    child_obj.parent = parent_obj

def parent_keep_transform(parent_obj, child_obj):
    parent(parent_obj, child_obj)
    child_obj.matrix_parent_inverse = parent_obj.matrix_world.inverted()

def parent_objects(parent_obj, child_objs):
    for child_obj in child_objs:
        parent(parent_obj, child_obj)

def parent_objects_keep_transform(parent_obj, child_objs):
    for child_obj in child_objs:
        parent_keep_transform(parent_obj, child_obj)

def clear_parent(child_obj):
    child_obj.parent = None

def clear_parent_keep_transform(child_obj):
    matrix = child_obj.matrix_world.copy()
    clear_parent(child_obj)
    child_obj.matrix_world = matrix

def unparent_objects(child_objs):
    for child_obj in child_objs:
        clear_parent(child_obj)

def unparent_objects_keep_transform(child_objs):
    for child_obj in child_objs:
        clear_parent_keep_transform(child_obj)

def delete_hierarchy(obj, remove_top_object=False):

    objects = [obj] if remove_top_object else []

    #Deselect All objects
    bpy.ops.object.select_all(action='DESELECT')

    # recursion
    def get_child_names(obj):
        for child in obj.children:
            objects.add(child)
            if child.children:
                get_child_names(child)

    get_child_names(obj)

    for object in objects:
        object.select_set(True)

    bpy.ops.object.delete()

def get_active_viewport(context, x, y):
    for area in context.screen.areas:
        if area.type != 'VIEW_3D':
            continue
        for region in area.regions:
            if region.type == 'WINDOW':
                if (x >= region.x and
                    y >= region.y and
                    x < region.width + region.x and
                    y < region.height + region.y):

                    return (area.spaces.active, region)
    return (None, None)

def get_all_viewports(context):

    viewports = []
    for area in context.screen.areas:
        if area.type != 'VIEW_3D':
            continue
        for region in area.regions:
            if region.type == 'WINDOW':
                viewports.append((area, region))

    return viewports

def coord_visible_in_region(region, coord):
    rv3d = region.data
    coords = view3d_utils.location_3d_to_region_2d(region, rv3d, coord)
    
    #location_3d_to_region_2d returns None if the 3d coordinate is begind the origin of perspective view
    if coords == None:
        return False

    if coords[0] < 0 or coords[1] < 0:
        return False
    
    if coords[0] > region.width or coords[1] > region.height:
        return False
    
    return True

def point_visible_in_any_region(context, coord):
    for area, region in get_all_viewports(context):
        if coord_visible_in_region(region, coord):
            return True
    return False

def object_to_promethean_name(object):
    return object.name

def objects_to_promethean_names(objects):
    return [object_to_promethean_name(object) for object in objects]

def get_object_by_promethean_name(name):
    try:
        return bpy.data.objects[name]
    except:
        return None

def get_objects_by_promethean_names(names):
    objects = [get_object_by_promethean_name(name) for name in names]
    
    #remove None objects:
    return [object for object in objects if object]

def import_fbx(file_path):
    bpy.ops.import_scene.fbx(filepath = file_path)
    return bpy.context.selected_objects

def import_obj(file_path):
    bpy.ops.import_scene.obj(filepath = file_path)
    return bpy.context.selected_objects

import_map = {
    "fbx": import_fbx,
    "obj": import_obj,
}

def import_asset(file_path):
    extension = file_path.split('.')[-1]

    if extension in import_map:
        return import_map[extension](file_path)

    return None

def link_object_from_blend_file(file_path, collection, objects=None):

    with bpy.data.libraries.load(file_path, link=True) as (data_from, data_to):
        if objects:
            #Link specified objects
            data_to.meshes = [name for name in data_from.meshes if name in objects]
        else:
            #Link All Objects
            data_to.meshes = data_from.meshes

    objects = []
    for mesh in data_to.meshes:
        #create new object referencing the mesh data block
        object = bpy.data.objects.new(mesh.name, mesh)
        objects.append(object)
        collection.objects.link(object)
    
    return objects

def delete_objects(objects):
    #Deselect All objects
    bpy.ops.object.select_all(action='DESELECT')

    #Select objects to be deleted
    for object in objects:
        object.select_set(True)

    #Delete
    bpy.ops.object.delete()

def try_get_existing_blend_data(file):

    try:
        libraries = bpy.data.libraries
        file_name = os.path.basename(file)

        # If there are two different files which share the same name
        # D:\assets\test.blend
        # D:\assets\high-res\test.blend
        # There is a key conflict, so we will have to iterate over all libraries

        if file_name in libraries:
            blend_data = libraries[file_name]

            # Check that it is actually the right file, also checks for key conflicts
            if blend_data.filepath == file:
                return blend_data

            return next(lib for lib in libraries if lib.filepath == file)
    except:
        return None

    return None

def create_objects_from_blend_data(blend_data, collection):
    
    objects = []
    for data in blend_data.users_id:
        if not type(data) == bpy.types.Mesh:
            continue
        
        obj = bpy.data.objects.new(data.name, data)
        objects.append(obj)
        collection.objects.link(obj)
        
    return objects

def asset_path_to_blend_path(asset_path):
    return asset_path + ".blend"

def get_bmesh(object):
    bm = bmesh.new()

    if object.mode == 'OBJECT':
        bm.from_mesh(object.data)
    else:
        bm = bmesh.from_edit_mesh(object.data)    

    return bm 

def update_bmesh(object, bm):
    if object.mode == 'OBJECT':
        bm.to_mesh(object.data)
    else:
        bmesh.update_edit_mesh(object.data)

# Ported from:
# https://github.com/blender/blender/blob/master/source/blender/blenkernel/intern/camera.c
# void BKE_camera_params_compute_viewplane(CameraParams *params, int winx, int winy, float aspx, float aspy)
# https://github.com/blender/blender/blob/master/source/blender/blenlib/intern/math_geom.c
# void perspective_m4(float mat[4][4],const float left,const float right,const float bottom,const float top, const float nearClip,const float farClip)
def create_perspective_projection_matrix(x=1920, y=1080, lens=50, clip_start=0.1, clip_end=100, x_asp=1, y_asp=1, shift_x=0, shift_y=0, sensor_width=36.0, sensor_height=18.0, sensor_fit='AUTO', zoom=2):
    y_cor = y_asp/x_asp

    if sensor_fit == 'AUTO' or sensor_fit == 'HORIZONTAL':
        sensor_size = sensor_width
    else:
        sensor_size = sensor_height
    
    if x > y:
        view_fac = x
    else:
        view_fac = y_cor * y
        
    pix_size = (sensor_size * clip_start) / lens
        
    pix_size /= view_fac
    
    pix_size *= zoom
        
    x_min = -0.5 * x
    y_min = -0.5 * y_cor * y
    x_max =  0.5 * x
    y_max =  0.5 * y_cor * y

    dx = shift_x * view_fac
    dy = shift_y * view_fac

    x_min += dx
    y_min += dy
    x_max += dx
    y_max += dy

    x_min *= pix_size
    x_max *= pix_size
    y_min *= pix_size
    y_max *= pix_size

    left = x_min
    right = x_max
    bottom = y_min
    top = y_max
    
    x_delta = right - left
    y_delta = top - bottom
    z_delta = clip_end - clip_start
    
    #Horizontal Zoom Factor
    m00 = clip_start * 2 / x_delta
    
    #Vertical Zoom Factor
    m11 = clip_start * 2 / y_delta
    
    m20 = (right + left) / x_delta
    m21 = (top + bottom) / y_delta
    
    #Near and Far Clip Plane Depth Remapper
    m22 = -(clip_end + clip_start) / z_delta
    m23 = (-2 * clip_start * clip_end) / z_delta
    
    #Z to W Component Copier
    m32 = -1

    matrix = mathutils.Matrix((
        (m00, 0, 0, 0),
        (0, m11, 0, 0),
        (m20, m21, m22, m23),
        (0, 0, m32, 0),
        ))
    
    return matrix

# Ported from:
# https://github.com/blender/blender/blob/master/source/blender/blenkernel/intern/camera.c
# void BKE_camera_params_compute_viewplane(CameraParams *params, int winx, int winy, float aspx, float aspy)
# https://github.com/blender/blender/blob/master/source/blender/blenlib/intern/math_geom.c
# void orthographic_m4(float matrix[4][4], const float left, const float right, const float bottom, const float top, const float nearClip, const float farClip)
def create_orthographic_projection_matrix(x=1920, y=1080, clip_start=0.1, clip_end=100, x_asp=1, y_asp=1, shift_x=0, shift_y=0, sensor_width=36.0, sensor_height=18.0, sensor_fit="AUTO", ortho_scale = 1, zoom = 2):
    y_cor = y_asp/x_asp
    
    if sensor_fit == 'AUTO':
        if x > y:
            sensor_fit = 'HORIZONTAL'
        else:
            sensor_fit = 'VERTICAL'
    
    if sensor_fit == 'HORIZONTAL':
        view_fac = x
    else:
        view_fac = y_cor * y
        
    pix_size = ortho_scale
        
    pix_size /= view_fac
    
    pix_size *= zoom
        
    x_min = -0.5 * x
    y_min = -0.5 * y_cor * y
    x_max =  0.5 * x
    y_max =  0.5 * y_cor * y

    dx = shift_x * view_fac
    dy = shift_y * view_fac

    x_min += dx
    y_min += dy
    x_max += dx
    y_max += dy

    x_min *= pix_size
    x_max *= pix_size
    y_min *= pix_size
    y_max *= pix_size

    left = x_min
    right = x_max
    bottom = y_min
    top = y_max
    
    x_delta = right - left
    y_delta = top - bottom
    z_delta = clip_end - clip_start
    
    m00 = 2 / x_delta
    m11 = 2 / y_delta
    
    m30 = -(right + left) / x_delta
    m31 = -(top + bottom) / y_delta
    m22 = -2 / z_delta
    m32 = -(clip_end + clip_start) / z_delta
    
    matrix = mathutils.Matrix((
        (m00, 0, 0, 0),
        (0, m11, 0, 0),
        (0, 0, m22, 0),
        (m30, m31, 0, 1),
        ))
    
    return matrix

def create_projection_matrix_for_viewport(viewport, width=0, height=0):
    area, region = viewport
    space = next(space for space in area.spaces if space.type == 'VIEW_3D')
    rv3d = region.data
    
    if width == 0 or height == 0:
        width = area.width
        height = area.height

    if rv3d.is_perspective:
        return create_perspective_projection_matrix(
            x=width, 
            y=height, 
            clip_start=space.clip_start, 
            clip_end=space.clip_end, 
            lens=space.lens + rv3d.view_camera_zoom
        )
    else:
        return create_orthographic_projection_matrix(
            x=width, 
            y=height, 
            clip_start=space.clip_start, 
            clip_end=space.clip_end, 
            ortho_scale = rv3d.view_distance,
        )

def get_triangle_positions(object):
    out_verts = []
    
    for polygon in object.data.polygons:
        verts = get_poly_verts(object, polygon)
        out_verts += verts
    
    return out_verts

def get_poly_verts(object, polygon):
    verts = []
    
    for loop_index in range(polygon.loop_start, polygon.loop_start + polygon.loop_total):
        vert_index = object.data.loops[loop_index].vertex_index
        vertex = object.data.vertices[vert_index]
        verts.append( [vertex.co[0], vertex.co[1], vertex.co[2]] )
    
    return verts

def create_transformation_matrix(translation=mathutils.Vector((0,0,0)), rotation=mathutils.Euler((0, 0, 0))):
    mat_rot = rotation.to_matrix()
    mat_loc = mathutils.Matrix.Translation(translation)
    return mat_loc @ mat_rot.to_4x4()

def triangulate_object(object):
    name = 'PROMETHEAN_TRIANGULATE'
    object.modifiers.new(name, "TRIANGULATE")
    bpy.context.view_layer.objects.active = object
    bpy.ops.object.modifier_apply(modifier=name)

# This is disgusting. I can't believe the fov isnt accessible through region data
# This scans a ring of points horizontally around the view origin, testing if they are visible.
# The angle between the camera forward and the first point not visible is half the field of view...
# I want to throw up
def approximate_viewport_fov(region, step=0.1):
    angle = 0

    view_pos = region.data.view_matrix.inverted().translation

    while(angle < 91):

        a = radians(angle)
        x = cos(a)
        y = sin(a)

        v = mathutils.Vector((y, 0, x))
        v.rotate(region.data.view_rotation)

        test_pos = view_pos - v

        if not coord_visible_in_region(region, test_pos):
            break

        angle += step
    
    return angle * 2
    

        
        