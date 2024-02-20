import bpy
from .utils import *

def create_objects_from_file(file_path, collection):

    from .tasks import create_blend_from_asset

    if not file_path.endswith(".blend"):
        native_blend_file = False
        blend_file_path = asset_path_to_blend_path(file_path)
    else:
        native_blend_file = True
        blend_file_path = file_path

    # Check if the file path has already been linked to this file, if so grab the mesh data from there
    existing = try_get_existing_blend_data(blend_file_path)
    if existing:
        print("PrometheanAI: Creating object from already linked data")
        return create_objects_from_blend_data(existing, collection)

    # Check if a blend file actually exists for this asset, if it doesnt, create one
    if not native_blend_file and not os.path.isfile(blend_file_path):
        print("PrometheanAI: Generating .blend file from mesh")
        create_blend_from_asset(file_path, blend_file_path, blocking=True)

    # Link from file on disk
    print("PrometheanAI: Linking object from .blend file")
    return link_object_from_blend_file(blend_file_path, collection)