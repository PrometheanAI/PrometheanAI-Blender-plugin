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
from os.path import dirname, abspath

#Get the PrometheanAI directory and add to path
dir = dirname(dirname(abspath(__file__)))

sys.path.append(dir)

from utils import import_asset

def delete_all():
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete()

def make_asset(asset_path, blend_file):
    #First clear the scene
    delete_all()
    
    #Delete Default Collection
    bpy.data.collections.remove(bpy.data.collections['Collection'])

    import_asset(asset_path)

    #Disable saving previous versions
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=blend_file)

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
        help="File path for asset",
    )

    parser.add_argument(
        "-b", "--blend_file", dest="blend_file", type=str, required=True,
        help="Where to write the .blend file",
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

    # Run the example function
    make_asset(args.asset_path, args.blend_file)

if __name__ == "__main__":
    main()
