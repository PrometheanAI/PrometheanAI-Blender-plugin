# Example usage for this script.
# blender.exe --background --python "C:\Path\To\File\install_addon.py" -- --addon_file="D:\Downloads\PrometheanBlender.zip"
#
# Notice:
# '--' causes blender to ignore all following arguments so python can use them.
#
# See blender --help for details.


from gettext import install
import bpy
import sys

from pathlib import Path

def install_addon(path):
    bpy.ops.preferences.addon_install(filepath=path)

    addon_name = Path(path).stem

    bpy.ops.preferences.addon_enable(module=addon_name)

    bpy.ops.wm.save_userpref()

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
        "-a", "--addon_file", dest="addon_file", type=str, required=True,
        help="File path for plugin",
    )

    args = parser.parse_args(argv)

    if not argv:
        parser.print_help()
        return

    if not args.addon_file:
        print("Error: --asset_path argument not given, aborting.")
        parser.print_help()
        return

    install_addon(args.addon_file)

if __name__ == "__main__":
    main()
