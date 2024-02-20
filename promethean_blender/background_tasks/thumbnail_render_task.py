# A script to generate thumbnails for mesh data stored in a blend file.
# Example Usage:
# blender --background --factory-startup --python "D:\Source Codes\Git\PrometheanAI\background_tasks\thumbnail_render_task.py" -- --blend_file "D:\assets\source\source_data.blend" --asset_names "Cube.001,Sphere,Suzanne" --resolution_x 512 --resolution_y 512 --output_dir "D:\assets\thumbs" --hdri "D:\assets\HDRIs\Blender Default\interior.exr" --sun_yaw 330 --sun_pitch 60 --angle_y 10

# Minimum required arguments: By default renders a thumbnail of all mesh data blocks in the .blend file
# blender --background --factory-startup --python "D:\Source Codes\Git\PrometheanAI\background_tasks\thumbnail_render_task.py" -- --blend_file "D:\assets\source\source_data.blend" --resolution_x 512 --resolution_y 512 --output_dir "D:\assets\thumbs"

# Notice:
# '--factory-startup' is used to avoid the user default settings from
#                     interfering with automated scene generation.
#
# '--' causes blender to ignore all following arguments so python can use them.
#
# See blender --help for details.

import bpy
import sys
from math import *
import mathutils
import os


def horz_to_vert_fov(fov, width, height):
    return 2 * atan( tan(fov / 2) * (height / width))
    
def vert_to_horz_fov(fov, width, height):
    return 2 * atan( tan(fov / 2) * (width / height))

def distance_1d(x1, x2):
    return abs(x1 - x2)

def get_bounding_box(object):
    return [object.matrix_world @ mathutils.Vector(corner) for corner in object.bound_box]

def get_axis_length(object, axis):
    min_z = None
    max_z = None

    for point in get_bounding_box(object):
        if max_z == None or point[axis] > max_z:
            max_z = point[axis]
        if min_z == None or point[axis] < min_z:
            min_z = point[axis]

    return distance_1d(min_z, max_z)

def calc_target_distance(object, padding, fov, render_width, render_height):

    width = get_axis_length(object, 0)
    depth = get_axis_length(object, 1)
    height = get_axis_length(object, 2)

    aspect_ratio = render_width / render_height

    fov = radians(fov)

    if aspect_ratio < 1:
        fov = vert_to_horz_fov(fov, render_width, render_height)
    else:
        fov = horz_to_vert_fov(fov, render_width, render_height)

    distance = (height / 2) / tan(fov / 2)

    distance += max(width, depth)

    return distance

def calc_position(target_location, horz_angle, vert_angle, distance):
    
    angle = radians(horz_angle)
    vertical_angle = radians(vert_angle)

    x = distance * cos(angle)
    y = distance * sin(angle)
    z = distance * sin(vertical_angle)
    
    return mathutils.Vector((x, y, z)) + target_location

def look_at(camera_location, point):
    direction = point - camera_location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    return rot_quat.to_euler()

def object_center(object):

    total = mathutils.Vector((0,0,0))

    points = get_bounding_box(object)

    for vector in points:
        total += vector
        
    return total / len(points)

def create_camera(object, fov, horz_angle, vert_angle, padding, render_width, render_height):
    target_location = object_center(object)
    dist = calc_target_distance(object, padding, fov, render_width, render_height)
    pos = calc_position(target_location, horz_angle, vert_angle, dist)
    rot = look_at(pos, target_location)

    collection = bpy.context.scene.collection
    camera_name = "Promethean Camera"
    cam = bpy.data.cameras.new(camera_name)
    cam.angle = radians(fov)
    cam_obj = bpy.data.objects.new(camera_name, cam)
    
    cam_obj.location = pos
    cam_obj.rotation_euler = rot
    collection.objects.link(cam_obj)

    bpy.ops.object.select_all(action='DESELECT')

    #Fill frame
    bpy.context.scene.camera = cam_obj
    object.select_set(True)    
    bpy.ops.view3d.camera_to_view_selected()    
    
    cam.angle = radians(fov + padding)

    return cam_obj

def configure_hdri(hdri_path):

    node_tree = bpy.context.scene.world.node_tree
    tree_nodes = node_tree.nodes


    tree_nodes.clear()

    node_background = tree_nodes.new(type='ShaderNodeBackground')


    node_environment = tree_nodes.new('ShaderNodeTexEnvironment')

    node_environment.image = bpy.data.images.load(hdri_path) # Relative path
    node_environment.location = -300,0


    node_output = tree_nodes.new(type='ShaderNodeOutputWorld')   
    node_output.location = 200,0


    links = node_tree.links
    link = links.new(node_environment.outputs["Color"], node_background.inputs["Color"])
    link = links.new(node_background.outputs["Background"], node_output.inputs["Surface"])


def configure_world(hdri=None, sun_yaw=None, sun_pitch=None, sun_brightness = 10, samples=8, brightness = 0.5):

    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.film_transparent = True
    bpy.context.scene.eevee.taa_render_samples = samples


    if hdri:
        bpy.context.scene.world.use_nodes = True
        configure_hdri(hdri)
    else:
        bpy.context.scene.world.color = (brightness, brightness, brightness)
        
    if sun_yaw and sun_pitch:
        
        sun_yaw = radians(sun_yaw)
        sun_pitch = radians(sun_pitch)
        
        
        light_name = "Promethean Light"
        
        # Create light datablock
        light_data = bpy.data.lights.new(name=light_name, type='SUN')
        light_data.energy = sun_brightness

        light_object = bpy.data.objects.new(name=light_name, object_data=light_data)

        bpy.context.collection.objects.link(light_object)

        light_object.location = (0, 0, 3)
        light_object.rotation_euler = (0, sun_pitch, sun_yaw)

def delete_all():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

def append_object_from_blend_file(file_path, collection, objects=None):

    with bpy.data.libraries.load(file_path) as (data_from, data_to):
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

def get_mesh_names_in_file(file_path):
    mesh_names = []

    with bpy.data.libraries.load(file_path) as (data_from, data_to):
        for mesh in data_from.meshes:
            mesh_names.append(mesh)

    return mesh_names

def make_thumbnails(blend_file, asset_names, render_width, render_height, out_dir, fov=50, horz_angle=300, vert_angle=45, padding=5, hdri=None, sun_yaw=None, sun_pitch=None, samples=8):
    delete_all()
    configure_world(hdri, sun_yaw, sun_pitch)

    bpy.context.scene.render.resolution_x = render_width
    bpy.context.scene.render.resolution_y = render_height

    if asset_names == "*":
        asset_names = get_mesh_names_in_file(blend_file)
    else:
        asset_names = asset_names.split(',')

    print(asset_names)

    for mesh_name in asset_names:
        objects = append_object_from_blend_file(blend_file, bpy.context.scene.collection, [mesh_name,])

        if len(objects) > 0:
            object = objects[0]
            camera = create_camera(object, fov, horz_angle, vert_angle, padding, render_width, render_height)

            bpy.context.scene.render.filepath = os.path.join(out_dir, mesh_name + ".png")
            bpy.ops.render.render(write_still = True)

            #Delete the camera and mesh
            bpy.ops.object.select_all(action='DESELECT')
            camera.select_set(True)
            object.select_set(True)
            bpy.ops.object.delete() 

def main():
    import sys       # to get command line args
    import argparse  # to parse options for us and print a nice help message

    # get the args passed to blender after "--", all of which are ignored by
    # blender so scripts may receive their own arguments
    argv = sys.argv

    if "--" not in argv:
        argv = []  # as if no args are passed
    else:
        argv = argv[argv.index("--") + 1:]  # get all args after "--"

    # When --help or no args are given, print this help
    usage_text = (
        "Run blender in background mode with this script:"
        "  blender --background --python " + __file__ + " -- [options]"
    )

    parser = argparse.ArgumentParser(description=usage_text)

    parser.add_argument(
        "--blend_file", dest="blend_file", type=str, required=True,
        help="Path to .blend file",
    )

    parser.add_argument(
        "--resolution_x", dest="resolution_x", type=int, required=True,
        help="X Resolution in pixels",
    )

    parser.add_argument(
        "--resolution_y", dest="resolution_y", type=int, required=True,
        help="Y Resolution in pixels",
    )

    parser.add_argument(
        "--output_dir", dest="output_dir", type=str, required=True,
        help="Folder in which to place rendered images",
    )

    parser.add_argument(
        "--asset_names", dest="asset_names", type=str, required=False, default='*',
        help="Names of mesh data blocks to create asset from (Comma seperated list)",
    )

    parser.add_argument(
        "--fov", dest="fov", type=float, required=False, default=40,
        help="Field of view in degrees of the rendered camera",
    )

    parser.add_argument(
        "--padding", dest="padding", type=float, required=False, default=5,
        help="Additional fov to add to camera to add gap around object border",
    )

    parser.add_argument(
        "--angle_x", dest="angle_x", type=float, required=False, default=300,
        help="Angle at which to orbit around the target object",
    )

    parser.add_argument(
        "--angle_y", dest="angle_y", type=float, required=False, default= 25,
        help="Angle at which to pitch up / down the target object",
    )

    parser.add_argument(
        "--sun_yaw", dest="sun_yaw", type=float, required=False, default= None,
        help="Yaw angle for sun light",
    )

    parser.add_argument(
        "--sun_pitch", dest="sun_pitch", type=float, required=False, default=None,
        help="Pitch angle for sun light",
    )

    parser.add_argument(
        "--samples", dest="samples", type=int, required=False, default= 8,
        help="Angle at which to pitch up / down the target object",
    )

    parser.add_argument(
        "--hdri", dest="hdri", type=str, required=False, default=None,
        help="File path to an HDRI image to use for lighting",
    )

    args = parser.parse_args(argv)

    if not argv:
        parser.print_help()
        return

    if not args.blend_file:
        print("Error: --blend_file argument not given, aborting.")
        parser.print_help()
        return

    if not args.asset_names:
        print("Error: --asset_names argument not given, aborting.")
        parser.print_help()
        return

    if not args.resolution_x:
        print("Error: --resolution_x argument not given, aborting.")
        parser.print_help()
        return

    if not args.resolution_y:
        print("Error: --resolution_y argument not given, aborting.")
        parser.print_help()
        return

    if not args.output_dir:
        print("Error: --output_dir argument not given, aborting.")
        parser.print_help()
        return

    make_thumbnails(args.blend_file, args.asset_names, args.resolution_x, args.resolution_y, args.output_dir, sun_yaw=args.sun_yaw, sun_pitch=args.sun_pitch, samples=args.samples, hdri=args.hdri, horz_angle=args.angle_x, vert_angle=args.angle_y, fov=args.fov, padding=args.padding)


if __name__ == "__main__":
    main()
