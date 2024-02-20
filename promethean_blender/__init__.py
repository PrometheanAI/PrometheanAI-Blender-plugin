
from multiprocessing import current_process

# Check to make sure we are in the main process, 
# subprocesses will automatically call __init__.py, but does not have access to blender's api
# this check makes sure that subprocesses never try to access blender's api
if current_process().name == 'MainProcess':
    from .operators import drag_drop_modal, server_manager
    from . import side_panel
    #from . import side_panel

def register():
    server_manager.register()
    drag_drop_modal.register()
    side_panel.register()


def unregister():
    side_panel.unregister()
    drag_drop_modal.unregister()
    server_manager.unregister()

bl_info = {
    "name" : "Promethean AI Blender",
    "author" : "Promethean AI Team",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Generic"
}