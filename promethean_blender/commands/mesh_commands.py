from lib2to3.pytree import convert
import bpy
import json
from mathutils import Vector, Euler, Quaternion
import os

from numpy import block

from ..import_file import create_objects_from_file

from ..utils import *
from ..constants import *

# See:
# https://docs.blender.org/api/current/bpy.types.Mesh.html

# add_objects_from_triangles {"obj1": {"name": "obj1", "verts": [[0.0,0.0,0.0], [1.0,0.0,0.0], [1.0,1.0,0.0], [0.0,1.0,0.0], [1.0,-1.0,0.0], [0.0,-1.0,0.0]], "tri_ids": [[0,1,2], [0,2,3], [0,1,5], [1,5,4]], "normals": [[0.0,1.0,0.0],[0.0,1.0,0.0],[0.0,1.0,0.0],[0.0,1.0,0.0]]}}
def add_objects_from_triangles(parameters_str):
    obj_list = json.loads(parameters_str)

    out_names = {}
    for dcc_name in obj_list:
        geometry_dict = obj_list[dcc_name]

        verts = geometry_dict[VERTICES_KEY]
        faces = geometry_dict[TRI_ID_KEY]
        name = geometry_dict[NAME_KEY]
        
        verts = [ [convert_in(x) for x in y] for y in verts ]

        #Create mesh from data
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(vertices=verts, edges=[], faces=faces)

        #Create object with mesh
        obj = bpy.data.objects.new(name, mesh)

        #Add To Scene
        bpy.context.view_layer.active_layer_collection.collection.objects.link(obj)

        if TRANSFORM_KEY in geometry_dict:
            transform = geometry_dict[TRANSFORM_KEY]

            obj.location = Vector(transform[TRANSLATION_KEY])
            obj.rotation_euler = euler_from_degrees(transform[ROTATION_KEY])
            obj.scale = Vector(transform[SCALE_KEY])

        out_names[dcc_name] = geometry_dict[NAME_KEY]
    return json.dumps(out_names)

def construct_vertex_dictionary(vertices):
    result = {}
    index = 0
    for vertex in vertices:
        v = Vector(vertex)
        v = v.freeze()
        if not v in result:
            result[v] = index
            index += 1
    return result

def construct_mesh(vertices, name, face_verts=4):
    num_verts = len(vertices)
    num_faces = num_verts // face_verts

    # Use a dictionary to remove duplicate verts
    index_dict = construct_vertex_dictionary(vertices)

    faces = [None] * num_faces

    for face_index in range(num_faces):
        face_indices = [None] * face_verts

        for vert_index in range(face_verts):
            vert = Vector( vertices[(face_index * face_verts) + vert_index])
            vert.freeze()

            face_indices[vert_index] = index_dict[vert]

        faces[face_index] = face_indices 

    verts = index_dict.keys()

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices=verts, edges=[], faces=faces)

    obj = bpy.data.objects.new(name, mesh)
    bpy.context.view_layer.active_layer_collection.collection.objects.link(obj)

    return obj

# add_objects_from_polygons {"name": "FixedFurnitureCoatCloset", "points": [[0.0, 0.0, 0.0], [103.69, 0.0, 0.0], [103.69, 0.0, 60.0], [0.0, 0.0, 60.0]], "transform": {"translation": [937.9074, 0.0, 192.8589], "rotation": [0,0,0], "scale": [1,1,1]}}
# add_object_from_polygons {"name": "FixedFurnitureCoatCloset", "points": [ [0.0, 0.0, 0.0], [103.69, 0.0, 0.0], [103.69, 0.0, 60.0], [0.0, 0.0, 60.0], [0.0, 0.0, 0.0], [103.69, 0.0, 0.0], [103.69, 60.0, 0.0], [0.0, 60.0, 0.0] ]}
def add_object_from_polygons(parameters_str):

    data = json.loads(parameters_str)
    obj = construct_mesh(data[POINTS_KEY], data[NAME_KEY])

    if TRANSFORM_KEY in data:
        transform = data[TRANSFORM_KEY]

        pos = Vector(transform[TRANSLATION_KEY])
        pos = convert_in(pos)
        obj.location = pos
        obj.rotation_euler = euler_from_degrees(transform[ROTATION_KEY])
        obj.scale = Vector(transform[SCALE_KEY])

# add_objects {"Group111": {"group": true, "name": "Group111", "location": [0,1,2], "rotation":[3,4,5], "scale":[1,1,1]}}
# add_objects {"NewMesh111": {"group": false, "name": "NewMesh111", "asset_path":"D:\\Desktop\\monkey.fbx" "location": [10,11,12], "rotation":[3,4,5], "scale":[1,2,3]}}

def add_objects(parameters_str):
    obj_dict = json.loads(parameters_str)
    return_dict = {}
    
    for object_name in obj_dict.keys():
        linked_object = add_object(obj_dict[object_name])
        return_dict[object_name] = object_to_promethean_name(linked_object)

    return json.dumps(return_dict)

def add_object(obj_dict):
    #If the object is a group, make an empty
    if obj_dict.get(GROUP_KEY, False):
        new_obj = bpy.data.objects.new(obj_dict[NAME_KEY], None)
        new_obj.empty_display_size = 0.1
        new_obj.empty_display_type = PLAIN_AXES

        bpy.context.collection.objects.link(new_obj)
    else:
        if obj_dict.get(ASSET_PATH_KEY, None):
            asset_path = obj_dict[ASSET_PATH_KEY]

            objects = create_objects_from_file(asset_path, bpy.context.collection)
            
            if len(objects) == 1:
                new_obj = objects[0]
        else:
            default_size = convert_in(100)
            bpy.ops.mesh.primitive_cube_add(size=default_size)
            new_obj = bpy.context.active_object
            new_obj.name = obj_dict[NAME_KEY]
            new_obj.location = Vector((0, 0, 0))

            #force blender to update the transformation matrix of new_obj
            bpy.context.view_layer.update()
            set_origin(new_obj, Vector((0, 0, -default_size * 0.5)))

    pos = Vector(obj_dict[LOCATION_KEY])
    pos = convert_in(pos)
    new_obj.location =  pos
    new_obj.rotation_euler = euler_from_degrees(obj_dict[ROTATION_KEY])
    new_obj.scale = Vector(obj_dict[SCALE_KEY])
    new_obj.name = obj_dict[NAME_KEY]

    parent_name = obj_dict.get('parent_dcc_name', None)
    if parent_name:
        parent_obj = get_object_by_promethean_name(parent_name)
        if parent_obj:
            #parent(parent_obj, new_obj)
            parent_keep_transform(parent_obj, new_obj)
        else:
            print('Parent to attach was not found: %s' % parent_name)

    return new_obj

def set_uv_quadrant(u=None, v=None):
    obj = bpy.context.active_object
    bm = get_bmesh(obj)
    uv_layer = bm.loops.layers.uv.verify()

    for face in bm.faces:
        if not face.select:
            continue

        for loop in face.loops:
            current_uv = loop[uv_layer].uv
            #extract decimal part and add to uv quadrant
            new_u = current_uv[0] if u == None else u + current_uv[0] % 1
            new_v = current_uv[1] if v == None else v + current_uv[1] % 1

            loop[uv_layer].uv = (new_u, new_v)

    update_bmesh(obj, bm)

def set_vertex_color(color):
    obj = bpy.context.active_object
    bm = get_bmesh(obj)
    color_layer = bm.loops.layers.color.verify()

    for face in bm.faces:
        if not face.select:
            continue

        for loop in face.loops:
            loop[color_layer] = color

    update_bmesh(obj, bm)

def select_vertex_color(objects, color):
    for object in objects:
        bm = get_bmesh(object)
        color_layer = bm.loops.layers.color.verify()

        for face in bm.faces:
            face.select_set(False)

            for loop in face.loops:
                if loop[color_layer] == color:
                    face.select_set(True)

        update_bmesh(object, bm)

def set_roughness(parameters_str):
    value = float(parameters_str)
    quadrant = int(lerp(-5, 5, value))
    set_uv_quadrant(u=quadrant)

def set_metallic(parameters_str):
    is_metallic, has_texture = parameters_str.split(' ')

    # -2 = metallic
    # 0 = has texture
    # -1 = non metallic

    v = -2 if is_metallic else 0 if has_texture else -1
    set_uv_quadrant(v=v)

def set_texture_tiling(parameters_str):
    has_texture, is_metallic = parameters_str.split(' ')
    v = 0 if has_texture else -2 if is_metallic else -1
    set_uv_quadrant(v=v)

def set_uv_quadrant_cmd(parameters_str):
    u, v = [int(x) for x in parameters_str.split(' ')]
    set_uv_quadrant(u=u, v=v)

def set_vertex_color_cmd(parameters_str):
    colors = [float(str(clr)) for clr in parameters_str.split(',')]
    color = Vector((colors[0], colors[1], colors[2], 1))
    set_vertex_color(color)

def select_vertex_color_cmd(parameters_str):
    object_names, color = parameters_str.split(' ')
    if type(object_names) != list:
        object_names = [object_names]

    color = [ float(clr)/255 for clr in color.split(',')]

    objects = get_objects_by_promethean_names(object_names)
    select_vertex_color(objects, Vector((color[0], color[1], color[2], 1)))

def get_vertex_colors(parameters_str):
    p_names = parameters_str.split(',')
    objs = get_objects_by_promethean_names(p_names)

    vertex_colors_data = dict()

    for obj in objs:
        vertex_data = set()
        vertex_colors = set()

        bm = get_bmesh(obj)
        color_layer = bm.loops.layers.color.verify()
        uv_layer = bm.loops.layers.uv.verify()

        for face in bm.faces:
            face.select_set(False)

            for loop in face.loops:
                uv = loop[uv_layer].uv
                color = loop[color_layer]
                color_copy = mathutils.Vector((color[0], color[1], color[2], color[3]))
                color_copy.freeze()
                

                if color_copy not in vertex_colors:
                    v = uv[1]

                    roughness = floor(uv[0] + 5) / 10.0
                    has_texture = 0 <= v <= 1
                    metalness = False if has_texture else v < -1

                    vertex_colors.add(color_copy)
                    vertex_data.add((color_copy[0], color_copy[1], color_copy[2], color_copy[3], roughness, metalness, has_texture))

        if vertex_data:
            vertex_colors_data[obj.name] = list(vertex_data)
    
    return json.dumps(vertex_colors_data)
