from cgitb import text
from http import server
import bpy
import textwrap

from . import constants

class SidePanel(bpy.types.Panel):
    bl_label = "Promethean AI"
    bl_category = "Promethean AI"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"

    def draw(self, context):
        global server_status

        layout = self.layout

        layout = self.layout
        scene = context.scene

        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column()
        col.separator()

        col.label(text=context.window_manager.promethean_server_status)

        if context.window_manager.promethean_server_status == constants.PROMETHEAN_SERVER_STATUS_CONNECTED:
            col.operator(constants.KILL_SERVER_OPERATOR_ID)
        else:
            col.operator(constants.BEGIN_SERVER_OPERATOR_ID)


        #if process:
        #    col.label(text=constants.PROMETHEAN_SERVER_RUNNING)
        #    col.operator(constants.KILL_SERVER_OPERATOR_ID)
        #else:
        #    col.label(text=constants.PROMETHEAN_SERVER_NOT_RUNNING)
        #    col.operator(constants.BEGIN_SERVER_OPERATOR_ID)

        return


def register():
    bpy.utils.register_class(SidePanel)


def unregister():
    bpy.utils.unregister_class(SidePanel)