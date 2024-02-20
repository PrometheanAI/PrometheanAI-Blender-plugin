import bpy
from bpy_extras import view3d_utils

import gpu
from gpu_extras.batch import batch_for_shader

from ..constants import *
from .. import utils

from mathutils import *

# See:
# https://docs.blender.org/api/current/bpy.types.Scene.html#bpy.types.Scene.ray_cast
# https://docs.blender.org/api/current/bpy_extras.view3d_utils.html
# https://docs.blender.org/api/current/bpy.types.Operator.html#modal-execution

# Global variables, used to access the last position, or to cancel the modal operation

do_cancel = False

last_position = None
has_active_viewport = None
last_normal = None

do_draw_bounds = True

def get_current_modal_result():
    return (has_active_viewport, last_position, last_normal)

# While the timer is running, try to convert mouse position to 3d coordinates. Uses raycasts and viewport unproject
class DragDropModalOperator(bpy.types.Operator):
    """Operator which runs in a timer, to report viewport position information"""
    bl_idname = DRAG_DROP_MODAL_ID
    bl_label = DRAG_DROP_MODAL_NAME
    draw_handler = None

    _timer = None

    shader = None

    #Indices to draw bounding box using blender vertex order
    indices = (
        (0, 1), (1, 2), (2, 3), (3, 0),
        (6, 5), (5, 4), (4, 7), (7, 6),
        (1, 5), (0, 4), (2, 6), (3, 7))

    def cancel(self, context):
        wm = bpy.context.window_manager
        wm.event_timer_remove(self._timer)
        bpy.types.SpaceView3D.draw_handler_remove(self.draw_handler, 'WINDOW')
        return {FINISHED}

    def draw_overlay(self):

        if not do_draw_bounds:
            return

        global last_position
        global last_normal
        self.shader.bind()
        self.shader.uniform_float("color", (1, 0, 0, 1))

        rotation_euler = utils.normal_to_euler(last_normal) #last_normal.to_track_quat('-Z', 'Y').to_euler()

        transform = utils.create_transformation_matrix(last_position, rotation_euler)

        #Example bounding box. Replace this with the object bounds in local space, which can be got from utils.get_bounding_box_local 
        bounds = [Vector((-1.0, -1.0, 0.0)), Vector((-1.0, -1.0, 2.0)), Vector((-1.0, 1.0, 2.0)), Vector((-1.0, 1.0, 0.0)), Vector((1.0, -1.0, 0.0)), Vector((1.0, -1.0, 2.0)), Vector((1.0, 1.0, 2.0)), Vector((1.0, 1.0, 0.0))]

        transformed = [transform @ pt for pt in bounds]

        batch = batch_for_shader(self.shader, 'LINES', {"pos": transformed}, indices=self.indices)
        batch.draw(self.shader)


    def modal(self, context, event):
        global do_cancel
        global last_position
        global last_normal
        global has_active_viewport

        if do_cancel:
            do_cancel = False
            return self.cancel(context)

        if event.type in {'RIGHTMOUSE', 'ESC'}:
            bpy.data.objects['Cube'].location = last_position
            bpy.data.objects['Cube'].rotation_euler = last_normal.to_track_quat('-Z', 'Y').to_euler()
            return self.cancel(context)

        if not event.type == EVENT_TIMER:
            return {PASS_THROUGH}

        space, region = utils.get_active_viewport(context, event.mouse_x, event.mouse_y)

        has_active_viewport = not space == None

        if space == None:
            return {PASS_THROUGH}

        # If there in an active viewport, calculate origin and vector, try a ray cast, if there is no result, use the viewport unproject

        region_view_3d = region.data

        viewport_relative_coords = event.mouse_x - region.x, event.mouse_y - region.y
        view_vector = view3d_utils.region_2d_to_vector_3d(region, region_view_3d, viewport_relative_coords)
        ray_origin = view3d_utils.region_2d_to_origin_3d(region, region_view_3d, viewport_relative_coords)
        
        deps = bpy.context.evaluated_depsgraph_get()

        result, location, normal, index, object, matrix = bpy.context.scene.ray_cast(deps, ray_origin, view_vector)
        if result:
            last_position = location
            last_normal = normal
        else:
            last_position = view3d_utils.region_2d_to_location_3d(region, region_view_3d, viewport_relative_coords, (0,0,0))
            last_normal = Vector((0, 0, 1))

        if context.area:
            context.area.tag_redraw()

        return {PASS_THROUGH}

    def execute(self, context):
        global do_cancel
        do_cancel = False
        wm = bpy.context.window_manager
        self._timer = wm.event_timer_add(0.01, window=bpy.context.window)
        wm.modal_handler_add(self)

        self.shader = gpu.shader.from_builtin('3D_UNIFORM_COLOR')
        self.draw_handler = bpy.types.SpaceView3D.draw_handler_add(self.draw_overlay, (), 'WINDOW', 'POST_VIEW')

        return {RUNNING_MODAL}

def end_drag_drop():
    global do_cancel

    do_cancel = True


class EndDragDrop(bpy.types.Operator):
    """EndDragDrop"""
    bl_idname = "object.promethean_end_drag_drop"
    bl_label = "End Promethean Drag Drop"

    @classmethod
    def poll(cls, context):
        return True
    
    def execute(self, context):
        end_drag_drop()
        return {'FINISHED'}

def register():
    bpy.utils.register_class(DragDropModalOperator)
    bpy.utils.register_class(EndDragDrop)

def unregister():
    bpy.utils.unregister_class(EndDragDrop)
    bpy.utils.unregister_class(DragDropModalOperator)