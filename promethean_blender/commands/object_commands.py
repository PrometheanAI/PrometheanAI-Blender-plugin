import bpy
import json

from ..utils import *

from ..constants import *

from ..import_file import *

from mathutils import Vector

def get_selection(parameters_str):
    objects = get_selected_mesh_objects()
    names = objects_to_promethean_names(objects)
    return str(names)

def get_visible_static_mesh_actors(parameters_str):
    visible_meshes = get_visible_mesh_objects()

    visible_in_camera = [obj for obj in visible_meshes if point_visible_in_any_region(bpy.context, obj.location)]

    return str(objects_to_promethean_names(visible_in_camera))

def get_selected_and_visible_static_mesh_actors(parameters_str):
    #visible_and_selected = get_selected_and_visible_mesh_objects()#

    #visible_in_camera = [obj for obj in visible_and_selected if point_visible_in_any_region(bpy.context, obj.location)]

    #return str(objects_to_promethean_names(visible_in_camera))

    selection = get_selected_mesh_objects()
    visible = get_objects_visible_in_camera()
    #Replace this with file name:
    scene_name = bpy.context.scene.name

    selected_paths_dict = {}
    for i, obj_name in enumerate(selection):
        selected_paths_dict.setdefault(get_reference_path(obj_name), []).append(i)

    rendered_paths_dict = {}
    for i, obj_name in enumerate(visible):
        rendered_paths_dict.setdefault(get_reference_path(obj_name), []).append(i)

    return json.dumps({'selected_names': objects_to_promethean_names(selection),
                          'rendered_names': objects_to_promethean_names(visible),
                          'selected_paths': selected_paths_dict,
                          'rendered_paths': rendered_paths_dict, 'scene_name': scene_name})



def get_location_data(parameters_str):

    obj_names = parameters_str.split(',')
    data_dict = {object_to_promethean_name(obj): list(convert_out(obj.location)) for obj in get_objects_by_promethean_names(obj_names) if obj}
    return json.dumps(data_dict)

def parent(parameters_str):
    object_names = parameters_str.split(',')
    objects = get_objects_by_promethean_names(object_names)
    parent_objects_keep_transform(objects[0], objects[1:])

def unparent(parameters_str):
    object_names = parameters_str.split(',')
    objects = get_objects_by_promethean_names(object_names)
    unparent_objects_keep_transform(objects)

def isolate_selection(parameters_str):
    unselected = get_unselected_objects()

    for object in unselected:
        object.hide_set(True)

def kill(parameters_str):
    selected = get_selected_mesh_objects()
    for obj in selected:
        obj.name = obj.name.replace(KILL_STR, '') if KILL_STR in obj.name else obj.name + KILL_STR

def translate(parameters_str):
    value, p_names = json.loads(parameters_str)
    value = Vector(value)
    value = convert_in(value)
    objects = get_objects_by_promethean_names(p_names)

    for object in objects:
        object.location = value

def translate_relative(parameters_str):
    value, p_names = json.loads(parameters_str)
    value = Vector(value)
    value = convert_in(value)
    objects = get_objects_by_promethean_names(p_names)

    for object in objects:
        object.location += value

def scale(parameters_str):
    value, p_names = json.loads(parameters_str)
    value = Vector(value)
    objects = get_objects_by_promethean_names(p_names)

    for object in objects:
        object.scale = value

def scale_relative(parameters_str):
    value, p_names = json.loads(parameters_str)
    value = Vector(value)
    objects = get_objects_by_promethean_names(p_names)

    bpy.ops.object.select_all(action='DESELECT')

    for object in objects:
        object.select_set(True)
        bpy.ops.transform.resize(value=value, orient_type='LOCAL')
        object.select_set(False)

    for object in objects:
        object.select_set(True)

def rotate(parameters_str):
    value, p_names = json.loads(parameters_str)
    value = euler_from_degrees(value)
    objects = get_objects_by_promethean_names(p_names)

    for object in objects:
        object.rotation_euler = value

def rotate_relative(parameters_str):
    value, p_names = json.loads(parameters_str)
    #euler = euler_from_degrees(value)
    objects = get_objects_by_promethean_names(p_names)

    for object in objects:
        #object.rotation_euler.rotate(euler)
        object.rotation_euler.rotate_axis("Z", radians(value[2]))
        object.rotation_euler.rotate_axis("Y", radians(value[1]))
        object.rotation_euler.rotate_axis("X", radians(value[0]))

def get_pivot_data(parameters_str):
    obj_names = parameters_str.split(',')
    data_dict = {object_to_promethean_name(x): list(get_transform(x)[1]) for x in
                     get_objects_by_promethean_names(obj_names) if x}
    msg = json.dumps(data_dict)

def rename(parameters_str):
    source_name, target_name = parameters_str.split(',')
    source_obj = get_object_by_promethean_name(source_name)
    if source_obj:
        source_obj.name = target_name
    return source_obj.name

def set_hidden(parameters_str):
    p_names = parameters_str.split(',')
    objects = get_objects_by_promethean_names(p_names)
    for object in objects:
        object.hide_set(True)

def set_visible(parameters_str):
    p_names = parameters_str.split(',')
    objects = get_objects_by_promethean_names(p_names)
    for object in objects:
        object.hide_set(False)

def select(parameters_str):
    p_names = parameters_str.split(',')
    objects = get_objects_by_promethean_names(p_names)
    for object in objects:
        object.select_set(True)

def remove(parameters_str):
    p_names = parameters_str.split(',')
    objects = get_objects_by_promethean_names(p_names)

    delete_objects(objects)

def remove_descendents(parameters_str):
    p_names = parameters_str.split(',')
    objects = get_objects_by_promethean_names(p_names)
    for object in objects:
        delete_hierarchy(object)

def get_object_transform_data(object):
    translation = list(object.location)
    rotation = list(object.rotation_euler)
    #convert from radians to degrees
    rotation = [degrees(x) for x in rotation]

    scale = list(object.scale)

    pivot = get_pivot(object)
    pivot_offset = convert_out(pivot)
    return {TRANSLATION_KEY: translation, ROTATION_KEY: rotation, SCALE_KEY: scale, PIVOT_OFFSET_KEY: pivot_offset}

def get_raw_object_data(object, predict_rotation=False, is_group=False):
    transform_data = get_object_transform_data(object)
    size, pivot = get_transform(object)

    translation = [convert_out(x) for x in transform_data[TRANSLATION_KEY]]
    rotation = transform_data[ROTATION_KEY]
    scale = transform_data[SCALE_KEY]
    pivot_offset = transform_data[PIVOT_OFFSET_KEY]

    transform = translation + rotation + scale

    parent_name = object_to_promethean_name(object.parent) if object.parent else NO_PARENT

    out_dict = {RAW_NAME_KEY: object_to_promethean_name(object), PARENT_NAME_KEY: parent_name, IS_GROUP_KEY: is_group,
                SIZE_KEY: size, ROTATION_KEY: rotation, PIVOT_KEY: pivot, PIVOT_OFFSET_KEY: pivot_offset, TRANSFORM_KEY: transform}

    if object.data.library:
        out_dict[ART_ASSET_PATH_KEY] = get_reference_path(object)

    return out_dict

def get_all_objects_raw_data(predict_rotation=False, selection=False):
    objs = bpy.data.objects if selection else get_selected_objects()

    object_data_array = []
    for object in objs:
        if KILL_STR not in object.name:
            is_group = object.type == OBJ_TYPE_EMPTY and len(object.children) > 0
            obj_data = get_raw_object_data(object, predict_rotation=predict_rotation, is_group=is_group)
            object_data_array.append(obj_data)

    return object_data_array

def learn(file_path, extra_tags=[], project=None, from_selection=False):
    raw_data = get_all_objects_raw_data(selection=from_selection)
    scene_id = bpy.data.filepath + '/'
    learning_data_to_file(file_path, raw_data, scene_id, extra_tags, project)

def learn_file(file_path, learn_file_path, extra_tags=[], project=None, from_selection=False):
    bpy.ops.wm.open_mainfile(filepath=file_path)
    learn(learn_file_path, extra_tags=extra_tags, project=project, from_selection=from_selection)

def learning_data_to_file(file_path, raw_data, scene_id, extra_tags=[], project=None):
    learning_dict = {'raw_data': raw_data, 'scene_id': scene_id}
    if len(extra_tags) > 0:
        learning_dict['extra_tags'] = extra_tags
    if project is not None:
        learning_dict['project'] = project
    with open(file_path, 'w') as f:
        f.write(json.dumps(learning_dict))

def clear_selection(parameters_str):
    bpy.ops.object.select_all(action='DESELECT')

def get_transform_data(parameters_str):
    obj_names = parameters_str.split(',')
    data_dict = {}
    for obj_name in obj_names:
        object = get_object_by_promethean_name(obj_name)
        if object:
            data = get_raw_object_data(object)
            data_dict[obj_name] = data[TRANSFORM_KEY] + data[SIZE_KEY] + data[PIVOT_OFFSET_KEY] + [data[PARENT_NAME_KEY]]
    return json.dumps(data_dict)

def get_vertex_data_from_scene_object(parameters_str):
    obj = get_object_by_promethean_name(parameters_str)
    verts = get_triangle_positions(obj)

    vert_list = [{i: vert for i, vert in enumerate(verts)}]
    vert_dict = {'vertex_positions': vert_list}

    return json.dumps(vert_dict)

def get_vertex_data_from_scene_objects(parameters_str):
    obj_names = json.loads(parameters_str)
    out_dict = dict()
    for obj_name in obj_names:
        obj = get_object_by_promethean_name(obj_name)

        triangulate_object(obj)

        if obj.type == 'MESH':
            vert_list = get_triangle_positions(obj)
            vert_list = [{i: vert for i, vert in enumerate(vert_list)}]
            out_dict[obj_name] = vert_list

    return json.dumps(out_dict)

def learn_file_cmd(parameters_str):
    learn_dict = json.loads(parameters_str.replace('learn_file ', ''))
    learn_file(learn_dict['file_path'], learn_dict['learn_file_path'], learn_dict['tagsg'], learn_dict['project'])
    return json.dumps(True)

def learn_cmd(parameters_str):
    cache_file_path, from_selection = parameters_str.rpartition(' ')[::2]
    from_selection = from_selection == 'True'  # bool from text
    return str(learn(cache_file_path, [], None, from_selection))

def translate_and_raytrace_objects(objects, location, raytrace_distance, max_normal_deviation, ignore_objects):
    # Hide objects
    visibilities = {}
    for object in ignore_objects:
        visibilities[object.name] = object.hide_get()
        object.hide_set(True)

    if not raytrace_distance:
        return
    
    deps = bpy.context.evaluated_depsgraph_get()
    down_vec = Vector((0, 0, -1))
    up_vec = Vector((0, 0, 1))

    for obj in objects:
        result, location, normal, index, hit_object, matrix = bpy.context.scene.ray_cast(deps, location, down_vec)

        if not result:
            continue

        if up_vec.dot(normal) > max_normal_deviation:
            obj.rotation_euler = normal_to_euler(normal)

        obj.location = location

    # Unhide objects

    for object in ignore_objects:
        visible = visibilities[object.name]
        object.hide_set(visible)

def translate_and_raytrace(parameters_str):
    location, raytrace_distance, obj_names, ignore_names  = json.loads(parameters_str)
    location = [ convert_in(float(x)) for x in location]
    raytrace_distance = convert_in(float(raytrace_distance))
    max_normal_deviation = 0

    objects = get_objects_by_promethean_names(obj_names)
    ignore_objects = get_objects_by_promethean_names(ignore_names)

    translate_and_raytrace_objects(objects, location, raytrace_distance, max_normal_deviation, ignore_objects)

def translate_and_snap(parameters_str):

    location, raytrace_distance, max_normal_deviation, obj_names, ignore_names  = json.loads(parameters_str)
    location = [convert_in(float(x)) for x in location]
    raytrace_distance = convert_in(float(raytrace_distance))
    max_normal_deviation = float(max_normal_deviation)

    objects = get_objects_by_promethean_names(obj_names)
    ignore_objects = get_objects_by_promethean_names(ignore_names)

    translate_and_raytrace_objects(objects, location, raytrace_distance, max_normal_deviation, ignore_objects)

def match_objects(parameters_str):
    p_names = parameters_str.split(',')
    return_dict = {}

    for p_name in p_names:
        for object in bpy.data.objects:
            if object.name == p_name:
                return_dict[p_name] == object.name
                break

    msg = json.dumps(return_dict)

def set_mesh_on_objects(mesh_path, objects):
    for object in objects:
        transform = object.matrix_world.copy()

        created_objs = create_objects_from_file(mesh_path, bpy.context.collection)

        for obj in created_objs:
            obj.matrix_world = transform

    delete_objects(objects)

def set_mesh(parameter_str):
    mesh_path, p_names = json.loads(parameter_str)
    objects = get_objects_by_promethean_names(p_names)
    set_mesh_on_objects(objects)

def set_mesh_on_selection(parameters_str):
    mesh_path = parameters_str
    objects = get_selected_mesh_objects()
    set_mesh_on_objects(mesh_path, objects)
    
def add_mesh_on_selection(parameters_str):
    mesh_paths = parameters_str.split(',')
    new_objs = []
    objs = get_selected_mesh_objects()
    for obj in objs:
        for mesh_file in mesh_paths:
            new_obj = create_objects_from_file(mesh_file, bpy.context.collection)
            new_obj.matrix_world = obj.matrix_world.copy()
            new_obj.select_set(True)
            new_objs.append(new_obj)
