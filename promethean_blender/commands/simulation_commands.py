import bpy

#from utils import get_objects_by_promethean_names, get_objects_visible_in_camera, is_object_visible_camera

from ..utils import *

from ..constants import *

# See:
# https://docs.blender.org/manual/en/latest/physics/rigid_body/world.html
# https://docs.blender.org/api/current/bpy.types.RigidBodyWorld.html

def get_rigidbody_group():
    if not RBD_GROUP_NAME in bpy.data.collections:
        bpy.data.collections.new(RBD_GROUP_NAME)
    return bpy.data.collections[RBD_GROUP_NAME]

def ensure_rigidbody_world():
    if bpy.context.scene.rigidbody_world == None:
        bpy.ops.rigidbody.world_add()

def remove_rigid_body_world(objects_to_maintain):

    results = dict()

    if objects_to_maintain:
        for object in objects_to_maintain:
            results[object.name] = object.matrix_world.copy()

    bpy.ops.rigidbody.world_remove()
    bpy.context.scene.frame_current = bpy.context.scene.frame_start

    if objects_to_maintain:
        for object in objects_to_maintain:
            object.matrix_world = results[object.name]

    bpy.data.collections.remove(bpy.data.collections[RBD_GROUP_NAME])

def add_object_to_rigid_body_world(object, type):

    if not object.name in bpy.context.scene.rigidbody_world.collection.objects:
        bpy.context.scene.rigidbody_world.collection.objects.link(object)

    object.rigid_body.type = type

def set_rigidbody_start():
    bpy.context.scene.rigidbody_world.point_cache.frame_start = bpy.context.scene.frame_start + 1

def set_rigidbody_end(num_frames=250):
    point_cache = bpy.context.scene.rigidbody_world.point_cache
    point_cache.frame_end = point_cache.frame_start + num_frames

def begin_simulation():
    #if the animation is playing, stop it ( animation_play() is responsible for both playing and pausing -_- )
    if bpy.context.screen.is_animation_playing:
        bpy.ops.screen.animation_play()

    bpy.context.scene.frame_current = bpy.context.scene.frame_start
    bpy.ops.screen.animation_play()

def stop_simulation():
    if bpy.context.screen.is_animation_playing:
        bpy.ops.screen.animation_play()

def get_potential_static_objects(dynamic_objects = list()):
    static_nodes = list()

    for default_name in DEFAULT_STATIC_NODE_NAMES:
        if default_name in bpy.data.objects:
            object = bpy.data.objects[default_name]
            if not object in dynamic_objects:
                static_nodes.append(object)

    visible_objects = get_objects_visible_in_camera()
    static_nodes.extend(visible_objects)

    return static_nodes


simulated_objects = list()

def create_simulation(active_objects, passive_objects):
    global simulated_objects

    ensure_rigidbody_world()
    simulated_objects = active_objects
    bpy.context.scene.rigidbody_world.collection = get_rigidbody_group()

    for object in passive_objects:
        add_object_to_rigid_body_world(object, RBD_PASSIVE)

    for object in active_objects:
        add_object_to_rigid_body_world(object, RBD_ACTIVE)

    set_rigidbody_start()
    set_rigidbody_end()


def enable_simulation_on_objects(parameters_str):
    object_names = parameters_str.split(',')
    active_objects = get_objects_by_promethean_names(object_names)

    active_objects = [object for object in active_objects if object.visible_get()]
    active_objects = [object for object in active_objects if is_object_visible_camera(object)]

    passive_objects = get_potential_static_objects(active_objects)
    
    create_simulation(active_objects, passive_objects)

def start_simulation(parameters_str):
    begin_simulation()

def cancel_simulation(parameters_str):
    global simulated_objects
    stop_simulation()
    remove_rigid_body_world(None)
    simulated_objects = list()

def end_simulation(parameters_str):
    global simulated_objects
    stop_simulation()
    remove_rigid_body_world(simulated_objects)
    simulated_objects = list()

def end_simulation(parameters_str):
    cancel_simulation(parameters_str)