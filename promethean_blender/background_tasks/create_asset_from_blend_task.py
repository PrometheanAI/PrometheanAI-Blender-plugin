# Example usage for this script.
# blender.exe --background --factory-startup --python "C:\Path\To\File\create_blend_from_asset.py" -- --asset_path="D:\Desktop\monkey.fbx --blend_file="D:\Desktop\monkey.blend"
#
# Notice:
# '--factory-startup' is used to avoid the user default settings from
#                     interfering with automated scene generation.
#
# '--' causes blender to ignore all following arguments so python can use them.
#
# See blender --help for details.


import bpy
import sys
import os
import re
import unicodedata
import hashlib

def get_unique_file_path(desired_path):
    """
    Finds the file path that doesn't exist yet in the same folder as the desired path
    :param desired_path: path that you'd use in case there are no files in the destination folder
    """
    if not os.path.exists(desired_path):
        return desired_path
    file_name, extension = os.path.splitext(os.path.basename(desired_path))
    folder = os.path.dirname(desired_path)
    new_file_path = ''
    i = 1
    while True:
        new_file_path = os.path.join(folder, '{}-{}{}'.format(file_name, i, extension))
        if not os.path.exists(new_file_path):
            break
        i += 1
    return os.path.normpath(new_file_path)

def asset_name_to_path(root_path, asset_name, blend_file):
    hash_dir = os.path.dirname(blend_file)
    path_hash = hashlib.md5(hash_dir.encode()).hexdigest()

    export_file_path = os.path.join(root_path, path_hash, '%s.blend' % asset_name)
    export_file_path = get_unique_file_path(export_file_path)
    return export_file_path

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

    print(objects)
    
    return objects

def ensure_dir(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def make_assets(asset_path, blend_file, asset_names):

    asset_names = asset_names.split(',')

    bpy.data.collections.remove(bpy.data.collections['Collection'])

    bpy.context.preferences.filepaths.save_version = 0

    created_files = list()

    for asset in asset_names:
        #out_path = os.path.join(asset_path, asset, asset + ".blend")
        out_path = asset_name_to_path(asset_path, asset, blend_file)
        print(out_path)

        delete_all()
        objects = append_object_from_blend_file(blend_file, bpy.context.scene.collection, [asset])

        if len(objects) > 0:

            ensure_dir(out_path)
            created_files.append(out_path)

            #Save as new blend file containing only the asset mesh data
            #Can also implement fbx export here if you want it
            bpy.ops.wm.save_as_mainfile(filepath=out_path)

    return created_files

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
        "-a", "--asset_path", dest="asset_path", type=str, required=True,
        help="File path for assets",
    )

    parser.add_argument(
        "-b", "--blend_file", dest="blend_file", type=str, required=True,
        help="Path to .blend file",
    )

    parser.add_argument(
        "-n", "--asset_names", dest="asset_names", type=str, required=True,
        help="Names of mesh data blocks to create asset from (Comma seperated list)",
    )

    args = parser.parse_args(argv)

    if not argv:
        parser.print_help()
        return

    if not args.asset_path:
        print("Error: --asset_path argument not given, aborting.")
        parser.print_help()
        return

    if not args.blend_file:
        print("Error: --asset_path argument not given, aborting.")
        parser.print_help()
        return

    if not args.asset_names:
        print("Error: --asset_path argument not given, aborting.")
        parser.print_help()
        return

    # Run the example function


    files = make_assets(args.asset_path, args.blend_file, args.asset_names)

    response = ','.join(x for x in files)

    # Add these strings to easily parse the response from blender stdout
    print("<BEGIN_PROMETHEAN_RESPONSE>" + response + "<END_PROMETHEAN_RESPONSE>")

if __name__ == "__main__":
    main()
