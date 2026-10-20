import bpy
from bpy.utils import register_class, unregister_class
import os 
from bpy.props import StringProperty, IntProperty, BoolProperty, FloatProperty, EnumProperty
import numpy as np
from bpy.types import Operator
from gpu_extras.batch import batch_for_shader
from mathutils import Matrix,  Vector
from bpy_extras.view3d_utils import location_3d_to_region_2d
import blf
import bmesh
from bpy_extras import view3d_utils
import gpu
import datetime
from .has_enum import *
from .utils import *

class EraseBrush(Operator):
    bl_label = "Select erase brush"
    bl_idname = "paint.erase_brush"
    
    def execute(self, context):
        current_brush = context.tool_settings.image_paint.brush

        if current_brush and current_brush.blend == 'MIX':
            current_brush.blend = 'ERASE_ALPHA'
        else:
            current_brush.blend = 'MIX'
        return {'FINISHED'}

class LineStroke(Operator):
    bl_label = "Use Line Stroke"
    bl_idname = "paint.line_stroke"
    
    press: BoolProperty()

    def execute(self, context):
        current_brush = context.tool_settings.image_paint.brush

        if current_brush:
            if self.press:
                current_brush.stroke_method = 'LINE'
            else:
                current_brush.stroke_method = 'SPACE'
        return {'FINISHED'}

# Shader for debug plane for "Mask by depth"  tool
vertex_shader = '''
    uniform mat4 u_ViewProjectionMatrix;
    in vec3 position;

    void main()
    {
        gl_Position = u_ViewProjectionMatrix * vec4(position, 1.0);
    }
'''

fragment_shader = '''
    uniform vec4 u_PlaneColor;
    out vec4 FragColor;

    void main()
    {
        FragColor = u_PlaneColor;
    }
'''

try:
    shader = gpu.types.GPUShader(vertex_shader, fragment_shader)
except Exception as e:
    shader = None

def create_plane_vertices(size):
    return [
        (-size, -size, 0.0), 
        (size, -size, 0.0),   
        (size, size, 0.0),    
        (-size, size, 0.0),   
    ]

plane_indices = [
    (0, 1, 2),  
    (0, 2, 3),  
]

def get_camera_view_matrix():
    rv3d = bpy.context.space_data.region_3d
    return rv3d.view_matrix.inverted()

def get_plane_world_positions(distance, size):
    view_matrix = get_camera_view_matrix()
    plane_offset = Vector((0, 0, -distance))
    plane_vertices = create_plane_vertices(size)
    return [
        tuple((view_matrix @ (Vector(v) + plane_offset)).to_3d())
        for v in plane_vertices
    ]

def draw_plane():
    # Draw debug plane for "Mask By Depth" tool
    try:
        scene = bpy.context.scene
        debugplane_props = getattr(scene, "debugplane_props", None)
        if not debugplane_props or not debugplane_props.show_plane:
            return  

        if shader is None:
            return

        transformed_vertices = get_plane_world_positions(
            debugplane_props.depth_distance,
            debugplane_props.plane_size
        )
        if len(transformed_vertices) < 3:
            return

        batch = batch_for_shader(shader, 'TRIS', {"position": transformed_vertices}, indices=plane_indices)
        if batch is None:
            return

        rv3d = bpy.context.space_data.region_3d
        view_projection_matrix = rv3d.perspective_matrix
        if view_projection_matrix is None:
            return

        with gpu.matrix.push_pop():
            gpu.matrix.load_projection_matrix(view_projection_matrix)
            gpu.state.depth_test_set('LESS')  

            shader.bind()
            shader.uniform_float("u_ViewProjectionMatrix", view_projection_matrix)
            shader.uniform_float("u_PlaneColor", debugplane_props.plane_color)
            batch.draw(shader)

            gpu.state.depth_test_set('NONE')  

    except Exception as e:
        print(f"Error while drawing plane: {e}")

class DepthMaskOperator(Operator):
    bl_idname = "paint.depth_mask_operator"
    bl_label = "Depth Mask Operator"

    def execute(self, context):
        scene = context.scene
        distance = scene.debugplane_props.depth_distance
        self.depth_mask_select(context, distance)
        return {'FINISHED'}

    def depth_mask_select(self, context, distance):
        view_3d = bpy.context.space_data.region_3d
        region = bpy.context.region
        rv3d = bpy.context.region_data

        obj = context.object
        if obj is None or obj.type != 'MESH':
            self.report({'WARNING'}, "No mesh object selected")
            return

        bpy.ops.object.mode_set(mode='EDIT')
        mesh = bmesh.from_edit_mesh(obj.data)

        for face in mesh.faces:
            face.select = False

        for face in mesh.faces:
            for vert in face.verts:
                vert_co_world = obj.matrix_world @ vert.co
                view_vector = view3d_utils.location_3d_to_region_2d(region, rv3d, vert_co_world)

                if view_vector:
                    depth = (view_3d.view_matrix @ vert_co_world).z
                    if abs(depth) < distance:
                        face.select = True
                        break
        bmesh.update_edit_mesh(obj.data)
        
        if context.object.mode != 'TEXTURE_PAINT':
            bpy.ops.object.mode_set(mode='TEXTURE_PAINT')

class AdjustDepthDistanceOperator(Operator):
    bl_idname = "paint.adjust_depth_distance_operator"
    bl_label = "Adjust Depth Distance with Mouse Movement"

    initial_mouse_x: IntProperty()
    initial_distance: FloatProperty()

    _draw_handler = None  

    def modal(self, context, event):
        scene = context.scene

        if event.type == 'MOUSEMOVE':
            delta = event.mouse_x - self.initial_mouse_x
            scene.debugplane_props.depth_distance = self.initial_distance + delta * 0.01

            for area in bpy.context.screen.areas:
                if area.type == 'VIEW_3D':
                    area.tag_redraw()

            return {'RUNNING_MODAL'}

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            bpy.ops.paint.depth_mask_operator()
            scene.debugplane_props.show_plane = False  
            self.remove_draw_handler()  
            return {'FINISHED'}

        elif event.type in {'ESC', 'RIGHTMOUSE'}:
            scene.debugplane_props.show_plane = False  
            self.remove_draw_handler()  
            return {'CANCELLED'}
        
        return {'RUNNING_MODAL'}

    def invoke(self, context, event):
        scene = context.scene
        self.initial_mouse_x = event.mouse_x
        self.initial_distance = scene.debugplane_props.depth_distance
        scene.debugplane_props.show_plane = True  
        
        self.add_draw_handler()

        context.window_manager.modal_handler_add(self)
        return {'RUNNING_MODAL'}

    def add_draw_handler(self):
        
        self._draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            draw_plane, (), 'WINDOW', 'POST_VIEW'
        )

    def remove_draw_handler(self):
        
        if self._draw_handler is not None:
            bpy.types.SpaceView3D.draw_handler_remove(self._draw_handler, 'WINDOW')
            self._draw_handler = None

class PaintSelectionOperator(Operator):
    bl_idname = "paint.paint_by_selection"
    bl_label = "Paint by Selection"
    bl_options = {'REGISTER', 'UNDO'}
    
    mode: StringProperty(default='POLYGON')
    
    start_pos = None
    end_pos = None
    is_drawing = False

    def invoke(self, context, event):

        if bpy.context.scene.other_props.operator_running:
            self.report({'WARNING'}, "Operator is already running.")
            return {'CANCELLED'}

        self.start_pos = (event.mouse_region_x, event.mouse_region_y)
        self.end_pos = (event.mouse_region_x, event.mouse_region_y)
        self.is_drawing = False

        args = (self, context)
        self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, args, 'WINDOW', 'POST_PIXEL')

        context.window_manager.modal_handler_add(self)
        bpy.context.scene.other_props.operator_running = True  
        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        # Check if user holding the mouse button
        if event.type == 'MOUSEMOVE':
            if self.is_drawing:
                self.end_pos = (event.mouse_region_x, event.mouse_region_y)
                context.area.tag_redraw()

        elif event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.start_pos = (event.mouse_region_x, event.mouse_region_y)
            self.is_drawing = True
            context.area.tag_redraw()

        elif event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.end_pos = (event.mouse_region_x, event.mouse_region_y)
            self.is_drawing = False
            self.detect_and_paint(context)

            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.context.scene.other_props.operator_running = False  
            return {'FINISHED'}

        elif event.type in {'RIGHTMOUSE', 'ESC'}:
            
            bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
            bpy.context.scene.other_props.operator_running = False  
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def detect_and_paint(self, context):
        if self.start_pos and self.end_pos:
            selection_box = self.get_selection_box()
            self.paint_selection(context, selection_box)
        else:
            self.report({'ERROR'}, "Selection coordinates are not set properly.")

    def get_selection_box(self):
        if self.start_pos and self.end_pos:
            min_x = min(self.start_pos[0], self.end_pos[0])
            max_x = max(self.start_pos[0], self.end_pos[0])
            min_y = min(self.start_pos[1], self.end_pos[1])
            max_y = max(self.start_pos[1], self.end_pos[1])
            return (min_x, max_x, min_y, max_y)
        else:
            return None

    def paint_selection(self, context, selection_box):
        initial_mode = context.active_object.mode

        if self.mode == 'POLYGON':
            self.paint_by_polygon(context, selection_box)
        elif self.mode == 'UV_ISLAND':
            self.paint_by_uv_island(context, selection_box)
        elif self.mode == 'PART':
            self.paint_by_object(context, selection_box)
        bpy.ops.object.mode_set(mode=initial_mode)

    def paint_by_polygon(self, context, selection_box):
        obj = context.active_object
        
        if obj and obj.type == 'MESH':
            
            if obj.mode != 'EDIT':
                bpy.ops.object.mode_set(mode='EDIT')

            bpy.ops.mesh.select_mode(type="FACE")

            bpy.ops.mesh.select_all(action='DESELECT')

            min_x, max_x, min_y, max_y = selection_box

            bpy.ops.view3d.select_box(xmin=min_x, xmax=max_x, ymin=min_y, ymax=max_y, mode='ADD')

            bpy.ops.object.mode_set(mode='OBJECT')

            self.apply_paint_to_selected_faces(context)
        else:
            self.report({'WARNING'}, "Active object is not a mesh or cannot enter edit mode.")

    def paint_by_uv_island(self, context, selection_box):
        obj = context.active_object
        if obj and obj.type == 'MESH':
            
            bpy.ops.object.mode_set(mode='EDIT')

            bpy.ops.mesh.select_mode(type="FACE")

            bpy.ops.mesh.select_all(action='DESELECT')

            min_x, max_x, min_y, max_y = selection_box
            bpy.ops.view3d.select_box(xmin=min_x, xmax=max_x, ymin=min_y, ymax=max_y, mode='ADD')

            bpy.ops.mesh.select_linked(delimit={'SEAM'})

            bpy.ops.object.mode_set(mode='OBJECT')

            self.apply_paint_to_selected_faces(context)
        else:
            self.report({'WARNING'}, "Active object is not a mesh or cannot enter edit mode.")

    def paint_by_object(self, context, selection_box):
        obj = context.active_object
        if obj and obj.type == 'MESH':
            
            bpy.ops.object.mode_set(mode='EDIT')

            bpy.ops.mesh.select_mode(type="FACE")

            bpy.ops.mesh.select_all(action='DESELECT')

            min_x, max_x, min_y, max_y = selection_box
            bpy.ops.view3d.select_box(xmin=min_x, xmax=max_x, ymin=min_y, ymax=max_y, mode='ADD')

            bpy.ops.mesh.select_linked(delimit={'NORMAL'})

            bpy.ops.object.mode_set(mode='OBJECT')

            self.apply_paint_to_selected_faces(context)
        else:
            self.report({'WARNING'}, "Active object is not a mesh or cannot enter edit mode.")

    def apply_paint_to_selected_faces(self, context):
        obj = context.active_object

        if obj and obj.mode == 'OBJECT':  
            
            bpy.ops.object.mode_set(mode='TEXTURE_PAINT')

            tool = bpy.context.workspace.tools.from_space_view3d_mode('PAINT_TEXTURE', create=False)
            fill_brush = None
            if tool:
                
                brush = bpy.context.tool_settings.image_paint.brush
                if brush:
                    
                    col = brush.color
                    fill_brush = bpy.data.brushes.get('Fill')
                    bpy.context.scene.tool_settings.image_paint.brush = fill_brush
                    
                    if fill_brush:
                        oldcol = fill_brush.color
                        fill_brush.color = col

            obj.data.use_paint_mask = True

            bpy.context.scene.tool_settings.image_paint.brush = bpy.data.brushes['Fill']

            bpy.ops.paint.image_paint(stroke=[{
                "name": "defaultStroke",
                "mouse": (0, 0),  
                "mouse_event": (0, 0),  
                "location": (0.0, 0.0, 0.0),  
                "pen_flip": False,
                "pressure": 1.0,
                "size": bpy.context.scene.tool_settings.unified_paint_settings.size,
                "time": 0.0,
                "is_start": True,
                "x_tilt": 0.0,  
                "y_tilt": 0.0,  
            }])
            if fill_brush:
                fill_brush.color = oldcol
            
            context.area.tag_redraw()

            bpy.context.scene.other_props.operator_running = False  
            return {'FINISHED'}
        else:
            bpy.context.scene.other_props.operator_running = False  
            self.report({'WARNING'}, "Active object is not a mesh or is not in object mode.")
            return {'CANCELLED'}

    def draw_callback_px(self, context, args):
        
        if not self.is_drawing or not self.start_pos or not self.end_pos or context is None or self is None:
            return

        min_x, max_x, min_y, max_y = self.get_selection_box()
        if min_x and max_x and min_y and max_y:
            vertices = [
                (min_x, min_y),
                (max_x, min_y),
                (max_x, max_y),
                (min_x, max_y),
                (min_x, min_y)
            ]
            
            shader = gpu.shader.from_builtin('UNIFORM_COLOR' if is_4_0_or_newer() else '2D_UNIFORM_COLOR')
            batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": vertices})

            shader.bind()
            shader.uniform_float("color", (1.0, 1.0, 1.0, 0.5))  
            batch.draw(shader)

    def cancel(self, context):
        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
        bpy.context.scene.other_props.operator_running = False
        return {'CANCELLED'}

class SCREEN_OT_crop_tool(Operator):
    bl_idname = "paint.crop_tool"
    bl_label = "Crop Tool"
    bl_description = "Draw a box to crop a screenshot"
    bl_options = {'REGISTER', 'UNDO'}

    start_x: IntProperty()
    start_y: IntProperty()
    end_x: IntProperty()
    end_y: IntProperty()
    mouse_dragging: BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return context.area.type == 'VIEW_3D'

    def modal(self, context, event):
        try:
            context.area.tag_redraw()

            if event.type == 'MOUSEMOVE':
                if self.mouse_dragging:
                    self.end_x = event.mouse_region_x
                    self.end_y = event.mouse_region_y

            elif event.type == 'LEFTMOUSE':
                if event.value == 'PRESS':
                    self.start_x = event.mouse_region_x
                    self.start_y = event.mouse_region_y
                    self.mouse_dragging = True
                elif event.value == 'RELEASE':
                    if self.mouse_dragging:
                        self.end_x = event.mouse_region_x
                        self.end_y = event.mouse_region_y
                        self.mouse_dragging = False

                        try:
                            self.take_screenshot_and_crop(context)
                        except Exception as e:
                            self.report({'ERROR'}, f"Screenshot failed: {str(e)}")
                            return {'CANCELLED'}

                        bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                        context.area.tag_redraw()
                        bpy.context.scene.other_props.operator_running = False
                        return {'FINISHED'}

            elif event.type in {'RIGHTMOUSE', 'ESC'}:
                if self.mouse_dragging:
                    self.mouse_dragging = False
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                context.area.tag_redraw()
                bpy.context.scene.other_props.operator_running = False
                return {'CANCELLED'}

            return {'RUNNING_MODAL'}
        
        except Exception as e:

            self.report({'ERROR'}, f"Modal error: {str(e)}")
            return {'CANCELLED'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':

            if bpy.context.scene.other_props.operator_running:
                self.report({'WARNING'}, "Operator is already running")
                return {'CANCELLED'}
            
            self.start_x = 0
            self.start_y = 0
            self.end_x = 0
            self.end_y = 0
            self.mouse_dragging = False
            
            self._handle = bpy.types.SpaceView3D.draw_handler_add(self.draw_callback_px, (context,), 'WINDOW', 'POST_PIXEL')
            context.window_manager.modal_handler_add(self)
            bpy.context.scene.other_props.operator_running = True
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}

    def draw_callback_px(self, context):
        if not self.mouse_dragging:
            return
        
        vertices = [
            (self.start_x, self.start_y),
            (self.start_x, self.end_y),
            (self.end_x, self.end_y),
            (self.end_x, self.start_y),
            (self.start_x, self.start_y)
        ]
        if is_4_0_or_newer():
            shader = gpu.shader.from_builtin('UNIFORM_COLOR')
        else:
            shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')
        batch = batch_for_shader(shader, 'LINE_STRIP', {"pos": vertices})

        shader.bind()
        shader.uniform_float("color", (1.0, 1.0, 1.0, 0.5))  
        batch.draw(shader)

        size_x = abs(self.end_x - self.start_x)
        size_y = abs(self.end_y - self.start_y)
        size_text = f"Size: {size_x} x {size_y}"

        region_width, region_height = context.region.width, context.region.height
        text_pos_x = min(self.start_x, self.end_x) + 10
        text_pos_y = min(self.start_y, self.end_y) + 10

        font_id = 0 
        blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
        if is_4_0_or_newer():
            blf.size(font_id, 20)
        else:
            blf.size(font_id, 20, 72)
        blf.position(font_id, text_pos_x, text_pos_y, 0)
        blf.draw(font_id, size_text)

    def is_operator_removed(self):
        try:
            _ = self.start_x
            return False
        except ReferenceError:
            return True

    def take_screenshot_and_crop(self, context):
        try:
            if self.start_x == self.end_x or self.start_y == self.end_y:
                self.report({'ERROR'}, "Region selected is too small")
                return {'CANCELLED'}   

            view_data = context.scene.view_data.add()
            region = context.region
            bpy.data.images['Render Result'].render_slots.active_index = 7
            region_3d = bpy.context.area.spaces.active.region_3d
            
            store_current_view(view_data, context)
            self.Render(context,view_data)
            
            filepath = bpy.data.filepath
            current_datetime = datetime.datetime.now().strftime("%H_%M_%S")
            folder = context.scene.other_props.tempsavingdir
            if bpy.data.is_saved:
                if bpy.app.tempdir ==context.scene.other_props.tempsavingdir:
                    folder = bpy.path.abspath("//HASCaptures/")

                    if not os.path.exists(folder):
                        os.makedirs(folder)
            filepath = os.path.join(folder, "has_sc_" + current_datetime)
            EXT = "png"
            filepath_final = filepath + "." + EXT
            i = 0
            while os.path.exists(bpy.path.abspath(filepath_final)):
                filepath_final = filepath + "_{:03d}.{:s}".format(i, EXT)
                i += 1

            view_data.image_name = name=bpy.path.basename(filepath_final)
            view_data.image_path = filepath_final

            render_result = bpy.data.images.get('Render Result')
            render_result.save_render(filepath_final)

            image_new = bpy.data.images.load(filepath_final)

            width = image_new.size[0]
            height = image_new.size[1]

            region_width = region.width
            region_height = region.height

            x_scale = context.scene.other_props.screen_capture_scale
            y_scale = context.scene.other_props.screen_capture_scale

            left = int(min(self.start_x, self.end_x) * x_scale)
            right = int(max(self.start_x, self.end_x) * x_scale)
            upper = int(min(self.start_y, self.end_y) * y_scale)
            lower = int(max(self.start_y, self.end_y) * y_scale)
            left = max(0, min(left, width))
            right = max(0, min(right, width))
            upper = max(0, min(upper, height))
            lower = max(0, min(lower, height))

            if left >= right:
                left, right = right, left

            if upper >= lower:
                upper, lower = lower, upper

            cropped_width = right - left
            cropped_height = lower - upper

            view_data.crop_startX= int(self.start_x * x_scale)
            view_data.crop_startY= int(self.start_y * x_scale)
            view_data.crop_endX= int(self.end_x * x_scale)
            view_data.crop_endY= int(self.end_y * x_scale)

            pixels = np.array(image_new.pixels[:]).reshape((height, width, 4)) 
            cropped_pixels = pixels[upper:lower, left:right, :]

            bpy.data.images.remove(image_new)

            cropped_image = bpy.data.images.new(
                name=bpy.path.basename(filepath_final),
                width=cropped_width,
                height=cropped_height,
                alpha=True 
            )

            cropped_image.pixels = cropped_pixels.flatten().tolist()

            cropped_image.filepath_raw = filepath_final
            cropped_image.file_format = 'PNG'

            cropped_image.save_render(filepath_final)

            check_views()
            bpy.data.images['Render Result'].render_slots.active_index = 0
            try:
                bpy.ops.image.external_edit(filepath=filepath_final)
            except RuntimeError as ex:
                self.report({'ERROR'}, str(ex))
            
            return {'FINISHED'}
        except Exception as e:
            self.report({'ERROR'}, f"Screenshot error: {str(e)}")
            return {'CANCELLED'}
    def Render(self, context,view_data):
        render = context.scene.render
        
        region = context.region
        bpy.context.scene.render.image_settings.file_format = 'PNG'
        bpy.context.scene.render.image_settings.color_mode = 'RGBA'
        bpy.context.scene.render.image_settings.color_depth = '8'
        bpy.context.scene.render.image_settings.compression = 0

        current_show_overlays = bpy.context.area.spaces.active.overlay.show_overlays
        bpy.context.area.spaces.active.overlay.show_overlays = False

        current_film_transparent = bpy.context.scene.render.film_transparent
        bpy.context.scene.render.film_transparent = True

        render.resolution_x = int(region.width * context.scene.other_props.screen_capture_scale)
        render.resolution_y = int(region.height * context.scene.other_props.screen_capture_scale)

        view_data.render_sizeX = render.resolution_x
        view_data.render_sizeY = render.resolution_y    

        render.resolution_percentage = 100
        bpy.ops.render.opengl()

        bpy.context.area.spaces.active.overlay.show_overlays = current_show_overlays
        bpy.context.scene.render.film_transparent = current_film_transparent
        
def store_current_view(view_props, context):
    # Store view matrix for image projection operations
    bpy.ops.object.mode_set(mode='OBJECT')
    prev_active = bpy.context.view_layer.objects.active
    
    space = context.area.spaces.active
    region = space.region_3d
    current_camera = bpy.context.scene.camera
    bpy.ops.object.camera_add()
    tempcamera = bpy.context.object 
    bpy.context.scene.camera = tempcamera
    ortho = not region.is_perspective
    
    if ortho:
        tempcamera.data.type = 'ORTHO'
    else:
        tempcamera.data.type = 'PERSP'

    region = bpy.context.space_data.region_3d
    old_lens = bpy.context.space_data.lens
    old_view_distance = region.view_distance

    new_lens = 50
    bpy.context.space_data.lens = new_lens
    if ortho:
        new_view_distance = old_view_distance * (new_lens / old_lens)
        region.view_distance = new_view_distance

    view_distance = region.view_distance
    lens = bpy.context.space_data.lens

    bpy.ops.view3d.camera_to_view()
    
    view_matrix = tempcamera.matrix_world
    view_props.loc = view_matrix.to_translation()
    view_props.rot = view_matrix.to_euler()

    if ortho:
        view_props.ortho = True
        view_props.ortho_scale = view_distance/(lens/76.5)

    view_props.focal = bpy.context.space_data.lens

    stored_view = (tempcamera.matrix_world.copy(), tempcamera.data.type)
    view_props.view = repr(stored_view)
    for area in bpy.context.screen.areas:
        if area.type == 'VIEW_3D':
            region = area.spaces.active.region_3d
            if region.view_perspective == 'CAMERA':
                bpy.ops.view3d.view_camera()  

    bpy.data.objects.remove(tempcamera, do_unlink=True)
    bpy.context.view_layer.objects.active = prev_active
    region.view_distance = old_view_distance
    bpy.context.space_data.lens = old_lens
    bpy.context.scene.camera = current_camera

def check_views():
    # Check for valid view data
    view_data = bpy.context.scene.view_data
    for i in reversed(range(len(view_data))):
        if view_data[i].image_name not in bpy.data.images:
            view_data.remove(i)

class ProjectApply(Operator):
    """Project edited image back onto the object"""
    bl_idname = "paint.has_project_apply"
    bl_label = "Project Apply"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Image Index", default=0)

    def execute(self, context):
        check_views()
        try:
            view_data = context.scene.view_data[self.index]
        except IndexError:
            self.report({'ERROR'}, "Invalid image index")
            return {'CANCELLED'}
        region_data = context.space_data.region_3d
        stored_view_matrix = (region_data.view_matrix.copy(), region_data.view_perspective)
        
        if context.mode != 'OBJECT':
            bpy.ops.object.mode_set(mode='OBJECT')
        
        prev_active = context.view_layer.objects.active
        prev_selected = context.selected_objects.copy()
        
        baseimage = bpy.data.images.get(view_data.image_name)

        if not baseimage:
            self.report({'ERROR'}, f"Image ({view_data.image_name}) not found")
            return {'CANCELLED'}

        start_x = view_data.crop_startX
        start_y = view_data.crop_startY
        end_x = view_data.crop_endX
        end_y = view_data.crop_endY

        img = bpy.data.images.load(view_data.image_path)

        if not img:
            self.report({'ERROR'}, f"Image ({view_data.image_path}) not found")
            return {'CANCELLED'}
        createdimage = create_image_with_overlay(view_data.render_sizeX, view_data.render_sizeY, img, end_x, end_y, start_x, start_y)
        if not createdimage:
            self.report({'ERROR'}, f"Image cannot be applied")
            return {'CANCELLED'}
            
        image_name = createdimage.name
        bpy.ops.object.camera_add(enter_editmode=False, align='VIEW', location=(0, 0, 0), rotation=(0, 0, 0))
        camera = context.object

        camera.data.lens = context.space_data.lens
        current_focal_length = camera.data.lens

        region_data.view_perspective = 'PERSP'

        bpy.context.scene.camera = camera
        
        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in prev_selected:
            obj.select_set(True)
        context.view_layer.objects.active = prev_active
        
        bpy.ops.paint.texture_paint_toggle()

        stored_view_str = view_data.view

        apply_view_data_to_camera(view_data, camera)

        bpy.ops.paint.project_image(image=image_name)

        bpy.ops.object.mode_set(mode='OBJECT')

        bpy.data.objects.remove(camera)

        bpy.data.images.remove(createdimage)
        bpy.data.images.remove(img)
        region_data.view_matrix, region_data.view_perspective = stored_view_matrix

        for obj in bpy.context.selected_objects:
            obj.select_set(False)
        for obj in prev_selected:
            obj.select_set(True)
        context.view_layer.objects.active = prev_active

        if prev_active.type == 'MESH':
            bpy.ops.paint.texture_paint_toggle()

        return {'FINISHED'}

def apply_view_data_to_camera(view_data, camera):
    # Get camera and assign view transform, to use further in texture projection
    prev_active = bpy.context.view_layer.objects.active
    stored_view_str = view_data.view

    camera.location = view_data.loc
    camera.rotation_euler = view_data.rot

    if view_data.ortho:

        camera.data.type = 'ORTHO'
        camera.data.ortho_scale = view_data.ortho_scale/1.06
    else:
        camera.data.type = 'PERSP'
        camera.data.lens = view_data.focal/2.0  

    bpy.context.view_layer.update()
    bpy.context.view_layer.objects.active = prev_active

def create_image_with_overlay(main_img_width, main_img_height, overlay_image, start_x, start_y, end_x, end_y):
    # Uncrop image based on loaded image, and previous size.
    if start_x > end_x:
        start_x, end_x = end_x, start_x

    if start_y > end_y:
        start_y, end_y = end_y, start_y
        
    main_image = bpy.data.images.new("MainImage", width=main_img_width, height=main_img_height)

    overlay_width = overlay_image.size[0]
    overlay_height = overlay_image.size[1]
    
    offset_x = max(0, start_x)
    offset_y = max(0, start_y)
    end_x = min(end_x, main_img_width)
    end_y = min(end_y, main_img_height)

    main_pixels = np.zeros((main_img_height, main_img_width, 4), dtype=np.float32)
    overlay_pixels = np.array(overlay_image.pixels[:]).reshape((overlay_height, overlay_width, 4))

    for y in range(overlay_height):
        for x in range(overlay_width):
            target_x = offset_x + x
            target_y = offset_y + y
            if target_x < end_x and target_y < end_y:
                main_pixels[target_y, target_x, :] = overlay_pixels[y, x, :]

    main_pixels_flat = main_pixels.flatten()
    main_image.pixels = main_pixels_flat.tolist()
    main_image.update()
    
    return main_image   

class ProjectRemove(Operator):
    """Remove the selected image from the project list"""
    bl_idname = "paint.project_remove"
    bl_label = "Remove Project Image"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Image Index", default=0)

    def execute(self, context):
        try:
            if context.scene.view_data[self.index].image_name:
                img = bpy.data.images.get(context.scene.view_data[self.index].image_name)
                if img:
                    if img.users == 0:
                        bpy.data.images.remove(img)
            context.scene.view_data.remove(self.index)
        except IndexError:
            self.report({'ERROR'}, "Invalid image index")
            return {'CANCELLED'}

        return {'FINISHED'}

class ProjectOpen(Operator):
    """Open the image in an external editor"""
    bl_idname = "paint.project_open"
    bl_label = "Open Project Image"
    bl_options = {'REGISTER', 'UNDO'}

    index: IntProperty(name="Image Index", default=0)

    def execute(self, context):
        try:
            image_name = context.scene.view_data[self.index].image_name
            filepath = context.scene.view_data[self.index].image_path
        except IndexError:
            self.report({'ERROR'}, "Invalid image index")
            return {'CANCELLED'}
        try:
            bpy.ops.image.external_edit(filepath=filepath)
        except RuntimeError as ex:
            self.report({'ERROR'}, str(ex))

        return {'FINISHED'}

class SetQEFolder(Operator):
    bl_idname = "paint.setquefolder"
    bl_label = "Set Images Folder"
    bl_options = {'REGISTER', 'UNDO'}

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(
        default="*.png;*.jpg;*.jpeg;*.tiff;*.bmp;*.exr;*.hdr",
        options={'HIDDEN'}
    )

    def execute(self, context):

        directory = os.path.dirname(self.filepath)
        user_filename = os.path.basename(self.filepath)

        context.scene.other_props.tempsavingdir = directory
        
        for area in context.screen.areas:
            if area.type == 'FILE_BROWSER':
                area.tag_redraw()
        
        return {'FINISHED'}
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

class ProjectBakeGet(Operator):
    """Edit a snapshot of the 3D Viewport in an external image editor"""
    bl_idname = "paint.projectbakeget"
    bl_label = "Project Edit"
    bl_options = {'REGISTER'}

    _proj_hack = [""]

    def execute(self, context):
        import os

        EXT = "png" 

        for image in bpy.data.images:
            image.tag = True
        obj = bpy.context.object

        if not obj.material_slots:
            return

        original_materials = [slot.material for slot in obj.material_slots]

        custom_material = bpy.data.materials.new(name="Custom_AO_Material")
        custom_material.use_nodes = True
        nodes = custom_material.node_tree.nodes
        links = custom_material.node_tree.links
        
        bpy.context.scene.eevee.gtao_quality = 1
        bpy.context.scene.eevee.use_gtao_bent_normals = False
        bpy.context.scene.eevee.use_gtao_bounce = False

        nodes.clear()

        output_node = nodes.new(type='ShaderNodeOutputMaterial')
        ao_node = nodes.new(type='ShaderNodeAmbientOcclusion')
        fresnel_node = nodes.new(type='ShaderNodeFresnel')
        transparent_bsdf_node = nodes.new(type='ShaderNodeBsdfTransparent')
        add_shader_node = nodes.new(type='ShaderNodeAddShader')

        set_default(fresnel_node, 'IOR', 1.5)
        custom_material.blend_method = 'CLIP'  
        custom_material.show_transparent_back = False  

        output_node.location = (600, 0)
        add_shader_node.location = (400, 0)
        ao_node.location = (0, 0)
        fresnel_node.location = (0, -200)
        transparent_bsdf_node.location = (200, -200)

        links.new(ao_node.outputs['AO'], add_shader_node.inputs[0])
        links.new(fresnel_node.outputs['Fac'], transparent_bsdf_node.inputs['Color'])
        links.new(transparent_bsdf_node.outputs['BSDF'], add_shader_node.inputs[1])
        links.new(add_shader_node.outputs['Shader'], output_node.inputs['Surface'])
        custom_material.use_backface_culling = True

        for slot in obj.material_slots:
            slot.material = custom_material

        try:
            bpy.ops.paint.image_from_view()
        except RuntimeError as ex:
            self.report({'ERROR'}, str(ex))
            return {'CANCELLED'}

        for i, mat in enumerate(original_materials):
            obj.material_slots[i].material = mat

        image_new = None
        for image in bpy.data.images:
            if not image.tag:
                image_new = image
                break

        if not image_new:
            self.report({'ERROR'}, "Could not make new image")
            return {'CANCELLED'}

        filepath = os.path.basename(bpy.data.filepath)
        filepath = os.path.splitext(filepath)[0]

        if bpy.data.is_saved:
            filepath = "//" + filepath
        else:
            filepath = os.path.join(bpy.app.tempdir, "project_edit")

        obj = context.object

        if obj:
            filepath += "_" + bpy.path.clean_name(obj.name)

        filepath_final = filepath + "." + EXT
        i = 0

        while os.path.exists(bpy.path.abspath(filepath_final)):
            filepath_final = filepath + "{:03d}.{:s}".format(i, EXT)
            i += 1

        image_new.name = bpy.path.basename(filepath_final)
        ProjectBakeGet._proj_hack[0] = image_new.name

        image_new.filepath_raw = filepath_final
        image_new.file_format = 'PNG'
        image_new.save()

        filepath_final = bpy.path.abspath(filepath_final)

        image_name = ProjectBakeGet._proj_hack[0]
        image = bpy.data.images.get((image_name, None))
        if image is None:
            self.report({'ERROR'}, rpt_("Could not find image '{:s}'").format(image_name))
            return {'CANCELLED'}

        image.reload()
        fix_image_colors_by_alpha(image.name)
        bpy.ops.paint.project_image(image=image_name)
        
        bpy.data.materials.remove(custom_material)
        bpy.data.images.remove(image)

        return {'FINISHED'}

class ProjectBakeApply(Operator):
    """Project edited image back onto the object"""
    bl_idname = "paint.projectbakeapply"
    bl_label = "Project Apply"
    bl_options = {'REGISTER'}

    def execute(self, _context):
        image_name = ProjectBakeGet._proj_hack[0]
        image = bpy.data.images.get((image_name, None))
        if image is None:
            self.report({'ERROR'}, rpt_("Could not find image '{:s}'").format(image_name))
            return {'CANCELLED'}

        image.reload()
        bpy.ops.paint.project_image(image=image_name)

        return {'FINISHED'}

classes = [
EraseBrush,
LineStroke,
DepthMaskOperator,
AdjustDepthDistanceOperator,
PaintSelectionOperator,
SCREEN_OT_crop_tool,
ProjectApply,
ProjectRemove,
ProjectOpen,
SetQEFolder,
ProjectBakeGet,
ProjectBakeApply,
]

addon_keymaps = []

def register():
    for cls in classes:
        register_class(cls)
    bpy.types.Scene.paint_mode = EnumProperty(
        items=[
            ('POLYGON', 'By Polygon', 'Paint by individual polygons'),
            ('UV_ISLAND', 'By UV Island', 'Paint by UV islands'),
            ('PART', 'By Part', 'Paint by Separate Part')],
        name="Paint Mode",
        description="Choose the selection mode"
    )
    wm = bpy.context.window_manager
    km = wm.keyconfigs.addon.keymaps.new(name='Image Paint', space_type='EMPTY')

    kmi = km.keymap_items.new("paint.erase_brush", 'E', 'PRESS', ctrl=False, shift=False)

    kmi_press = km.keymap_items.new("paint.line_stroke", 'W', 'PRESS', ctrl=False, shift=False)
    kmi_press.properties.press = True 

    kmi_release = km.keymap_items.new("paint.line_stroke", 'W', 'RELEASE', ctrl=False, shift=False)
    kmi_release.properties.press = False

    addon_keymaps.append(km)
def unregister():
    for cls in reversed(classes):
        unregister_class(cls)
        
    del bpy.types.Scene.paint_mode
    
    wm = bpy.context.window_manager
    for km in addon_keymaps:
        try:
            wm.keyconfigs.addon.keymaps.remove(km)
        except Exception:
            pass