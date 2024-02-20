from importlib.resources import path
import bpy
import mathutils
import os
import json
import gpu
from ..constants import PROMETHEAN_MESSAGE_PREFIX, PROMETHEAN_MESSAGE_SUFFIX

from ..tasks import create_asset_from_blend

from ..import_file import create_objects_from_file

from ..utils import *
from ..operators.drag_drop_modal import get_current_modal_result

def get_scene_name(parameters):
    file_path = bpy.data.filepath

    if file_path == None:
        return 'None'
    
    return os.path.basename(file_path)

def save_current_scene(parameters):
    bpy.ops.wm.save_mainfile()

def open_scene(file_path):
    bpy.ops.wm.open_mainfile('INVOKE_DEFAULT', filepath=file_path, display_file_selector=False)

def raytrace(parameters_str):
    direction_vec, distance, p_names  = json.loads(parameters_str)
    direction_vec = mathutils.Vector(direction_vec)
    distance =  convert_in(distance)
    result_dict = {}

    #raycast from object origin, hide object so the ray doesn't collide with itself
    for name in p_names:
        object = get_object_by_promethean_name(name)
        if object:

            hidden = object.hide_get()
            object.hide_set(True)

            deps = bpy.context.evaluated_depsgraph_get()
            size, origin = get_transform(object)
            result, location, normal, index, hit_object, matrix = bpy.context.scene.ray_cast(deps, origin, direction_vec, distance=distance)

            result_dict[name] = [ convert_out(x) for x in location] if result else [0.0, 0.0, 0.0]

            object.hide_set(hidden)
    return result_dict

def toggle_surface_snapping(parameters_str):
    bpy.context.scene.tool_settings.use_snap = not bpy.context.scene.tool_settings.use_snap
    if bpy.context.scene.tool_settings.use_snap:
        bpy.context.scene.tool_settings.snap_elements = {'FACE'}

def screenshot(parameters_str):
    viewports = get_all_viewports()
    viewport = viewports[0]
    area, region = viewport

    path = parameters_str.strip()

    override = bpy.data.context.copy()

    override['area'] = area

    file_path = path

    temp = bpy.context.scene.render.filepath
    bpy.context.scene.render.filepath = file_path

    bpy.ops.render.opengl(override, write_still=True)
    
    bpy.context.scene.render.filepath = temp

def screenshot_manual():
    viewports = get_all_viewports()
    viewport = viewports[0]
    area, region = viewport
    context = bpy.context
    rv3d = region.data
    space = next(space for space in area.spaces if space.type == 'VIEW_3D')

    width = area.width
    height = area.height

    offscreen = gpu.types.GPUOffScreen(width, height)

    projection_matrix = create_projection_matrix_for_viewport(viewport)

    offscreen.draw_view3d(
        scene=context.scene,
        view_layer=context.view_layer,
        view3d=space,
        region=region,
        view_matrix=rv3d.view_matrix,
        projection_matrix=projection_matrix,
        do_color_management=True
        )

    buffer = offscreen.texture_color.read()

def start_dragging_asset(parameters_str):
    bpy.ops.wm.promethean_dragdrop_modal()

def asset_drop_finished(parameters_str):
    bpy.ops.object.promethean_end_drag_drop()
    has_viewport, position, normal = get_current_modal_result()
    if has_viewport:

        objects = create_objects_from_file(parameters_str, bpy.context.collection)

        rotation_euler = normal_to_euler(normal)

        print("Normal:")
        print(normal)

        for object in objects:
            object.location = position
            object.rotation_euler = rotation_euler

def get_camera_info(parameters_str):
    viewports = get_all_viewports(bpy.context)

    if(viewports):
        area, region = viewports[0]
        rv3d = region.data

        pos = rv3d.view_matrix.inverted().translation
        dir = rv3d.view_rotation.to_euler()

        # if you want the direction as a vector direction:
        # forward = mathutils.Vector((0, 0, 1))
        # forward.rotate(region.data.view_rotation)
        # forward = -forward #invert because blender camera is backwards

        fov = approximate_viewport_fov(region)

        pos = convert_out(pos)
        info_dict = {'camera_location': pos, 'camera_direction': dir, 'fov': fov, 'objects_on_screen': objects_to_promethean_names(get_objects_visible_in_camera())}
        return json.dumps(info_dict)

def create_assets_from_selection(parameters_str):
    content_folder = parameters_str


    # File must be saved for function to run
    if len(bpy.data.filepath) == 0:
        bpy.ops.wm.save_mainfile('INVOKE_AREA')
        return None

    selected = get_selected_mesh_objects()

    if len(selected) == 0:
        print("PrometheanAI: No Assets Selected")
        return None

    bpy.ops.wm.save_mainfile()

    response = create_asset_from_blend(content_folder, bpy.data.filepath, selected, blocking=True)

    print("Response:")
    print(response)

    print("Files:")

    #Get text between prefix and suffix
    response = response.split(PROMETHEAN_MESSAGE_PREFIX)[1]
    response = response.split(PROMETHEAN_MESSAGE_SUFFIX)[0]

    files = response.split(',')

    print(files)

    return json.dumps(files)