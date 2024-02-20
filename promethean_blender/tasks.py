from sys import stdout
import bpy
import os
import subprocess

from .background_tasks import create_blend_from_asset_task, create_asset_from_blend_task

def get_blender_executable():
    return bpy.app.binary_path

def run_process(args, blocking=True):
    process = subprocess.Popen(args)

    #Hide the cmd window on windows
    startupinfo = None
    if os.name == 'nt':
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    if blocking:
        process=subprocess.Popen(args, startupinfo=startupinfo, stdout=subprocess.PIPE, encoding='utf-8')
        data = process.communicate()
        #return stdout
        return data[0]
    else:
        process=subprocess.Popen(args, startupinfo=startupinfo)

def create_blend_from_asset(asset_path, blend_file, blocking=True):
    py_file = os.path.abspath(create_blend_from_asset_task.__file__)

    return run_process(
        [get_blender_executable(), 
        "--background", 
        "--factory-startup", 
        "--python", 
        py_file, 
        "--", 
        "--asset_path", 
        asset_path,
        "--blend_file",
        blend_file],
        blocking=blocking
        )

def create_asset_from_blend(asset_path, blend_file, objects, blocking=True):
    py_file = os.path.abspath(create_asset_from_blend_task.__file__)
    mesh_data_names = set()

    for object in objects:
        mesh_data_names.add(object.data.name)

    names_list = ','.join(mesh_data_names)

    return run_process(
        [get_blender_executable(), 
        "--background", 
        "--factory-startup", 
        "--python", 
        py_file, 
        "--", 
        "--asset_path", 
        asset_path,
        "--blend_file",
        blend_file,
        "--asset_names",
        names_list
        ],
        blocking=blocking
        )