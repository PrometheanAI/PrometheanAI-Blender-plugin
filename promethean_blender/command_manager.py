from .commands import mesh_commands, simulation_commands, scene_commands, object_commands, misc_commands

import bpy

# temporary function to use for commands I haven't implemented yet
def no_op(parameters_str):
    pass

# some commands in the maya and 3dsmax plugins just return none? i suppose they arent implemented
def return_none(parameters_str):
    return 'None'

def internal_server_error(parameters_str):
    print("PrometheanAI Internal Server Error: " + parameters_str)

# All commands are a function which takes one parameter, a string containing parameters from Promethean
command_dictionary = {
    "get_scene_name": scene_commands.get_scene_name,
    "save_current_scene": scene_commands.save_current_scene,
    "open_scene": scene_commands.open_scene,
    "get_selection": object_commands.get_selection,
    "get_visible_static_mesh_actors": object_commands.get_visible_static_mesh_actors,
    "get_selected_and_visible_static_mesh_actors": object_commands.get_selected_and_visible_static_mesh_actors,
    "get_location_data": object_commands.get_location_data,
    "get_pivot_data": object_commands.get_pivot_data,
    "get_transform_data": object_commands.get_transform_data,
    "add_objects": mesh_commands.add_objects,
    "add_objects_from_polygons": mesh_commands.add_object_from_polygons,
    "add_objects_from_triangles": mesh_commands.add_objects_from_triangles,
    "parent": object_commands.parent,
    "unparent": object_commands.unparent,
    # Removed match_objects command, told it was not needed due to blender using unique names
    # "match_objects": object_commands.match_objects,
    "isolate_selection": object_commands.isolate_selection,
    "learn_file": object_commands.learn_file_cmd,
    "get_vertex_data_from_scene_objects": object_commands.get_vertex_data_from_scene_objects,
    "get_vertex_data_from_scene_object": object_commands.get_vertex_data_from_scene_object,
    "report_done": misc_commands.report_done,
    "screenshot": scene_commands.screenshot,
    "kill": object_commands.kill,
    "rename": object_commands.rename,
    "learn": object_commands.learn_cmd,
    "set_vertex_color": mesh_commands.set_vertex_color_cmd,
    "set_roughness": mesh_commands.set_roughness,
    "set_metallic": mesh_commands.set_metallic,
    "set_texture_tiling": mesh_commands.set_texture_tiling,
    "set_uv_quadrant": mesh_commands.set_uv_quadrant_cmd,
    "get_vertex_colors": mesh_commands.get_vertex_colors,
    "select_vertex_color": mesh_commands.select_vertex_color_cmd,
    "add_mesh_on_selection": object_commands.add_mesh_on_selection,
    "translate": object_commands.translate,
    "scale": object_commands.scale,
    "rotate": object_commands.rotate,
    "translate_relative": object_commands.translate_relative,
    "scale_relative": object_commands.scale_relative,
    "rotate_relative": object_commands.rotate_relative,
    "translate_and_snap": object_commands.translate_and_snap,
    "translate_and_raytrace": object_commands.translate_and_raytrace,
    "set_mesh": object_commands.set_mesh,
    "set_mesh_on_selection": object_commands.set_mesh_on_selection,
    "remove": object_commands.remove,
    "remove_descendents": object_commands.remove_descendents,
    "set_hidden": object_commands.set_hidden,
    "set_visible": object_commands.set_visible,
    "select": object_commands.select,
    "create_assets_from_selection": scene_commands.create_assets_from_selection,
    "drop_asset": scene_commands.asset_drop_finished,
    "start_dragging_asset": scene_commands.start_dragging_asset,
    "asset_drop_finished": scene_commands.asset_drop_finished,
    "raytrace": scene_commands.raytrace,
    "raytrace_bidirectional": scene_commands.raytrace,
    "get_simulation_on_actors_by_name": return_none,
    "get_transform_data_from_simulating_objects": return_none,
    "enable_simulation_on_objects": simulation_commands.enable_simulation_on_objects,
    "start_simulation": simulation_commands.start_simulation,
    "cancel_simulation": simulation_commands.cancel_simulation,
    "end_simulation": simulation_commands.end_simulation,
    "toggle_surface_snapping": scene_commands.toggle_surface_snapping,
    "clear_selection": object_commands.clear_selection,
    "get_camera_info": scene_commands.get_camera_info, # Just send first [0] viewport
    "internal_server_error": internal_server_error
}

# List of commands which should push an undo state
undo_commands = ["add_objects", "add_objects_from_polygons", "add_objects_from_triangles", "parent", "unparent", "set_vertex_color", "set_roughness", "set_metallic", "set_texture_tiling", "set_uv_quadrant",
"add_mesh_on_selection", "translate", "scale", "rotate", "translate_relative", "scale_relative", "rotate_relative", "translate_and_snap", "translate_and_raytrace", "set_mesh", "set_mesh_on_selection", "remove",
"remove_descendents", "drop_asset", "asset_drop_finished", "enable_simulation_on_objects", "clear_selection"]

def do_command(command, parameters_str):
    if command in command_dictionary:
        function = command_dictionary[command]

        if command in undo_commands:
            bpy.ops.ed.undo_push(message="Promethean AI: " + command)

        response = function(parameters_str)

        response = response or 'None'

        return response

def handle_message(data):
    message_str = str(data.decode())
    for command_str in message_str.split('\n'):
        if not command_str:
            continue

        command, _, command_parameters_str = command_str.partition(' ')

        if not command:
            continue
        print("")
        print("PrometheanAI: " + command_str)
        print("")
        response = do_command(command, command_parameters_str)

        return response
